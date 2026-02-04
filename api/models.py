"""
Pydantic Models for Noon-E-Commerce API
"""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field


# Request Models
class PriceHistoryParams(BaseModel):
    days: int = Field(default=30, ge=1, le=30, description="Number of days of history")


# Response Models
class ProductResponse(BaseModel):
    sku: str
    name: str
    category: Optional[str] = None
    brand: Optional[str] = None
    active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    products: List[ProductResponse]
    total: int
    page: int
    page_size: int


class PricePoint(BaseModel):
    date: date
    price: float
    original_price: Optional[float] = None
    discount_pct: Optional[float] = None
    seller_id: str
    in_stock: bool


class PriceHistoryResponse(BaseModel):
    sku: str
    product_name: Optional[str] = None
    currency: str = "SAR"
    history: List[PricePoint]
    min_price: float
    max_price: float
    avg_price: float
    price_change_pct: Optional[float] = None


class CompetitorPrice(BaseModel):
    seller_id: str
    seller_name: Optional[str] = None
    price: float
    original_price: Optional[float] = None
    discount_pct: Optional[float] = None
    in_stock: bool
    last_updated: datetime


class CompetitorResponse(BaseModel):
    sku: str
    product_name: Optional[str] = None
    competitors: List[CompetitorPrice]
    lowest_price: float
    highest_price: float
    seller_count: int


class PriceAlert(BaseModel):
    sku: str
    product_name: Optional[str] = None
    previous_price: float
    current_price: float
    change_amount: float
    change_pct: float
    seller_id: str
    alert_type: str  # "price_drop" or "price_increase"
    detected_at: datetime


class DailyAlertsResponse(BaseModel):
    date: date
    alerts: List[PriceAlert]
    total_drops: int
    total_increases: int


class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
