"""
Noon-E-Commerce FastAPI Backend v2
With user authentication, SKU management, and admin features
"""

import os
import time
import uuid
import logging
from datetime import datetime
from typing import Optional
from functools import lru_cache
from contextvars import ContextVar

# Request ID context variable for correlation
request_id_ctx: ContextVar[str] = ContextVar('request_id', default='')

from fastapi import FastAPI, HTTPException, Depends, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_fastapi_instrumentator import Instrumentator
from tracing import setup_tracing

# Import routes
from routes_auth import router as auth_router
from routes_skus import router as skus_router
from routes_admin import router as admin_router
from routes_alerts import router as alerts_router

# Legacy imports for backward compatibility
from models import (
    ProductListResponse, ProductResponse,
    PriceHistoryResponse, CompetitorResponse,
    DailyAlertsResponse, HealthResponse, ErrorResponse
)
from database import db as clickhouse_db

# Configuration
API_TOKEN = os.environ.get('API_TOKEN')
if not API_TOKEN:
    raise RuntimeError("API_TOKEN environment variable is required")
RATE_LIMIT_REQUESTS = int(os.environ.get('RATE_LIMIT_REQUESTS', 100))
RATE_LIMIT_WINDOW = int(os.environ.get('RATE_LIMIT_WINDOW', 60))
CACHE_TTL = int(os.environ.get('CACHE_TTL', 300))

# CORS Origins from environment (comma-separated) or defaults for local dev
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',')
if not CORS_ORIGINS or CORS_ORIGINS == ['']:
    CORS_ORIGINS = ["http://localhost:3000", "http://localhost:3001"]

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Cache storage
cache_store: dict = {}


# FastAPI App
app = FastAPI(
    title="Noon-E-Commerce API",
    description="Market Intelligence API with User Authentication",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Rate limit handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Prometheus metrics instrumentation
# Exposes /metrics endpoint with RED metrics (Rate, Errors, Duration)
Instrumentator().instrument(app).expose(app, include_in_schema=True, tags=["Monitoring"])

# OpenTelemetry tracing (optional, enabled via OTEL_ENABLED=true)
setup_tracing(app)

# CORS - Origins loaded from CORS_ORIGINS env var
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# Request Correlation ID Middleware
@app.middleware("http")
async def add_correlation_id(request, call_next):
    # Get existing request ID from header or generate new one
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    request_id_ctx.set(request_id)
    
    # Add request ID to logging context
    start_time = time.time()
    
    response = await call_next(request)
    
    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000
    
    # Add headers to response
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
    
    # Log request with correlation ID
    logger.info(f"[{request_id}] {request.method} {request.url.path} - {response.status_code} - {duration_ms:.2f}ms")
    
    return response


# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    # Add HSTS only if you're serving over HTTPS
    # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Include routers
app.include_router(auth_router)
app.include_router(skus_router)
app.include_router(admin_router)
app.include_router(alerts_router)


# Startup and Shutdown Events
@app.on_event("startup")
async def startup_event():
    logger.info("Noon-E-Commerce API starting up...")
    logger.info(f"Environment: CORS_ORIGINS={CORS_ORIGINS}")
    # Verify database connection on startup
    if clickhouse_db.health_check():
        logger.info("ClickHouse connection verified")
    else:
        logger.warning("ClickHouse connection failed on startup")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Noon-E-Commerce API shutting down gracefully...")
    # Clear cache
    cache_store.clear()
    logger.info("Cache cleared")
    # Close database connections if needed
    logger.info("Shutdown complete")


# Caching helper
def get_cached(key: str):
    if key in cache_store:
        data, timestamp = cache_store[key]
        if time.time() - timestamp < CACHE_TTL:
            return data
    return None


def set_cached(key: str, data):
    cache_store[key] = (data, time.time())


# Legacy token auth for backward compatibility
async def verify_legacy_token(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization format")
    if parts[1] != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return parts[1]


# Health endpoint
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint"""
    db_status = "connected" if clickhouse_db.health_check() else "disconnected"
    return HealthResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        database=db_status,
        timestamp=datetime.utcnow()
    )


# Legacy endpoints for backward compatibility with existing frontend
@app.get("/prices/latest", tags=["Legacy"])
async def get_latest_prices(token: str = Depends(verify_legacy_token)):
    """Get latest prices (legacy endpoint)"""
    cache_key = "prices:latest"
    cached = get_cached(cache_key)
    if cached:
        return cached
    
    try:
        prices = clickhouse_db.get_latest_prices()
        response = {"prices": prices}
        set_cached(cache_key, response)
        return response
    except Exception as e:
        logger.error(f"Error getting latest prices: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@app.get("/products", response_model=ProductListResponse, tags=["Legacy"])
async def list_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    active_only: bool = Query(default=True),
    token: str = Depends(verify_legacy_token)
):
    """List all products (legacy endpoint)"""
    cache_key = f"products:{page}:{page_size}:{active_only}"
    cached = get_cached(cache_key)
    if cached:
        return cached
    
    try:
        products, total = clickhouse_db.get_products(page, page_size, active_only)
        response = ProductListResponse(
            products=[ProductResponse(**p) for p in products],
            total=total,
            page=page,
            page_size=page_size
        )
        set_cached(cache_key, response)
        return response
    except Exception as e:
        logger.error(f"Error listing products: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@app.get("/products/{sku}/price-history", response_model=PriceHistoryResponse, tags=["Legacy"])
async def get_price_history(
    sku: str,
    days: int = Query(default=30, ge=1, le=30),
    token: str = Depends(verify_legacy_token)
):
    """Get price history (legacy endpoint)"""
    cache_key = f"price_history:{sku}:{days}"
    cached = get_cached(cache_key)
    if cached:
        return cached
    
    try:
        result = clickhouse_db.get_price_history(sku, days)
        if not result:
            raise HTTPException(status_code=404, detail=f"No history for SKU: {sku}")
        response = PriceHistoryResponse(**result)
        set_cached(cache_key, response)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting price history: {e}")
        raise HTTPException(status_code=500, detail="Database error")


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8096)
