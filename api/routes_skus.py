"""
SKU/Watchlist Management API Routes for Noon-E-Commerce
Phase 4: User-scoped endpoints with pagination, search, sort, bulk import
"""

import re
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, validator

from auth import get_current_user, TokenPayload
from db_postgres import WatchlistDB, ProductDB

router = APIRouter(prefix="/api/skus", tags=["SKUs"])


# ============================================
# Pydantic Models
# ============================================

class SKUCreate(BaseModel):
    """Add SKU to watchlist"""
    sku_code: str
    target_price: Optional[float] = None
    
    @validator('sku_code')
    def validate_sku(cls, v):
        # Noon SKU format: N followed by numbers and letters
        if not re.match(r'^N[A-Za-z0-9]+$', v):
            raise ValueError('Invalid Noon SKU format (should start with N)')
        return v.upper()


class SKUUpdate(BaseModel):
    """Update watchlist item"""
    target_price: Optional[float] = None
    notify_on_drop: Optional[bool] = None


class SKUBulkCreate(BaseModel):
    """Bulk import SKUs"""
    sku_codes: List[str]
    
    @validator('sku_codes')
    def validate_skus(cls, v):
        if len(v) > 100:
            raise ValueError('Maximum 100 SKUs per bulk import')
        valid = []
        for sku in v:
            if re.match(r'^N[A-Za-z0-9]+$', sku):
                valid.append(sku.upper())
        return valid


class SKUResponse(BaseModel):
    """Single SKU/watchlist response"""
    id: int
    sku: str
    product_name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None
    target_price: Optional[float] = None
    notify_on_drop: bool = True
    created_at: str
    
    class Config:
        from_attributes = True


class SKUListResponse(BaseModel):
    """Paginated SKU list response"""
    items: List[SKUResponse]
    total: int
    page: int
    page_size: int
    pages: int


class BulkImportResponse(BaseModel):
    """Bulk import result"""
    created: int
    skipped: int
    sku_codes: List[str]


# ============================================
# Helper Functions
# ============================================

def format_sku_response(item: dict) -> SKUResponse:
    """Format watchlist item as SKU response"""
    return SKUResponse(
        id=item['id'],
        sku=item['sku'],
        product_name=item.get('product_name'),
        brand=item.get('brand'),
        category=item.get('category'),
        url=item.get('url'),
        image_url=item.get('image_url'),
        target_price=float(item['target_price']) if item.get('target_price') else None,
        notify_on_drop=item.get('notify_on_drop', True),
        created_at=str(item['created_at'])
    )


# ============================================
# Endpoints
# ============================================

@router.get("", response_model=SKUListResponse)
async def list_skus(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(default=None, max_length=100, description="Search by SKU or product name"),
    sort_by: str = Query(default='created_at', description="Sort field"),
    sort_order: str = Query(default='desc', pattern='^(asc|desc)$', description="Sort order"),
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    List user's tracked SKUs with pagination and search.
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (1-100, default: 20)
    - **search**: Filter by SKU code or product name
    - **sort_by**: Sort by created_at, target_price, or sku
    - **sort_order**: asc or desc
    """
    user_id = int(current_user.sub)
    
    items, total = WatchlistDB.list_by_user(
        user_id=user_id,
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    pages = (total + page_size - 1) // page_size  # Ceiling division
    
    return SKUListResponse(
        items=[format_sku_response(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.post("", response_model=SKUResponse, status_code=status.HTTP_201_CREATED)
async def add_sku(
    data: SKUCreate,
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Add a new SKU to track.
    
    - **sku_code**: Noon SKU (starts with N)
    - **target_price**: Optional price alert threshold
    """
    user_id = int(current_user.sub)
    
    # Check for duplicate
    existing = WatchlistDB.get_by_sku(user_id, data.sku_code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SKU already being tracked"
        )
    
    item = WatchlistDB.add(
        user_id=user_id,
        sku=data.sku_code,
        target_price=data.target_price
    )
    
    # Fetch with product info
    item = WatchlistDB.get_by_id(item['id'], user_id)
    return format_sku_response(item)


@router.get("/{sku_id}", response_model=SKUResponse)
async def get_sku(
    sku_id: int,
    current_user: TokenPayload = Depends(get_current_user)
):
    """Get SKU details by watchlist ID"""
    user_id = int(current_user.sub)
    
    item = WatchlistDB.get_by_id(sku_id, user_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SKU not found in your watchlist"
        )
    
    return format_sku_response(item)


@router.put("/{sku_id}", response_model=SKUResponse)
async def update_sku(
    sku_id: int,
    data: SKUUpdate,
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Update SKU settings.
    
    - **target_price**: Price alert threshold
    - **notify_on_drop**: Enable/disable price drop notifications
    """
    user_id = int(current_user.sub)
    
    updates = data.dict(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    item = WatchlistDB.update(sku_id, user_id, **updates)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SKU not found in your watchlist"
        )
    
    return format_sku_response(item)


@router.delete("/{sku_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sku(
    sku_id: int,
    current_user: TokenPayload = Depends(get_current_user)
):
    """Remove SKU from tracking"""
    user_id = int(current_user.sub)
    
    deleted = WatchlistDB.delete(sku_id, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SKU not found in your watchlist"
        )


@router.post("/bulk", response_model=BulkImportResponse)
async def bulk_import_skus(
    data: SKUBulkCreate,
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Bulk import SKUs to watchlist.
    
    - Maximum 100 SKUs per request
    - Invalid SKU formats are silently skipped
    - Duplicates are skipped
    """
    user_id = int(current_user.sub)
    
    if not data.sku_codes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid SKU codes provided"
        )
    
    created = WatchlistDB.bulk_add(user_id, data.sku_codes)
    
    return BulkImportResponse(
        created=len(created),
        skipped=len(data.sku_codes) - len(created),
        sku_codes=[item['sku'] for item in created]
    )


@router.get("/sku/{sku_code}", response_model=SKUResponse)
async def get_sku_by_code(
    sku_code: str,
    current_user: TokenPayload = Depends(get_current_user)
):
    """Get SKU details by SKU code"""
    user_id = int(current_user.sub)
    
    # Normalize SKU code
    sku_code = sku_code.upper()
    
    item = WatchlistDB.get_by_sku(user_id, sku_code)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SKU not found in your watchlist"
        )
    
    return format_sku_response(item)


# ============================================
# Price History (ClickHouse)
# ============================================

class PricePoint(BaseModel):
    """Single price point"""
    date: str
    price: float
    original_price: Optional[float] = None
    discount_pct: Optional[float] = None
    in_stock: bool = True


class PriceHistoryResponse(BaseModel):
    """Price history response"""
    sku: str
    product_name: Optional[str] = None
    current_price: Optional[float] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    avg_price: Optional[float] = None
    history: List[PricePoint]


@router.get("/{sku_id}/price-history", response_model=PriceHistoryResponse)
async def get_price_history(
    sku_id: int,
    days: int = Query(default=30, ge=1, le=90, description="Days of history"),
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Get price history for a tracked SKU.
    
    - **days**: Number of days of history (1-90, default: 30)
    
    Returns price points from ClickHouse with statistics.
    """
    user_id = int(current_user.sub)
    
    # Verify user owns this SKU
    item = WatchlistDB.get_by_id(sku_id, user_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SKU not found in your watchlist"
        )
    
    sku_code = item['sku']
    
    # Try to get price history from ClickHouse
    try:
        from database import NoonDatabase
        clickhouse = NoonDatabase()
        result = clickhouse.get_price_history(sku_code, days)
        
        if result and result.get('history'):
            history = [
                PricePoint(
                    date=str(p['date']),
                    price=p['price'],
                    original_price=p.get('original_price'),
                    discount_pct=p.get('discount_pct'),
                    in_stock=p.get('in_stock', True)
                )
                for p in result['history']
            ]
            prices = [p.price for p in history]
            return PriceHistoryResponse(
                sku=sku_code,
                product_name=item.get('product_name'),
                current_price=prices[0] if prices else None,
                min_price=min(prices) if prices else None,
                max_price=max(prices) if prices else None,
                avg_price=round(sum(prices) / len(prices), 2) if prices else None,
                history=history
            )
    except Exception:
        pass  # Fall back to empty history
    
    # Return empty history if ClickHouse unavailable
    return PriceHistoryResponse(
        sku=sku_code,
        product_name=item.get('product_name'),
        current_price=None,
        min_price=None,
        max_price=None,
        avg_price=None,
        history=[]
    )
