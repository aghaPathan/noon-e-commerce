"""
Admin API Routes for Noon-E-Commerce
Phase 5: Admin endpoints for user management and global SKU view
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from auth import get_current_admin, TokenPayload
from db_postgres import UserDB, WatchlistDB, ProductDB, get_stats

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ============================================
# Pydantic Models
# ============================================

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: str
    updated_at: Optional[str] = None


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    page_size: int


class UserUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
    full_name: Optional[str] = None


class WatchlistItemResponse(BaseModel):
    id: int
    user_email: str
    sku: str
    product_name: Optional[str] = None
    target_price: Optional[float] = None
    created_at: str


class WatchlistListResponse(BaseModel):
    items: List[WatchlistItemResponse]
    total: int
    page: int
    page_size: int


class ProductResponse(BaseModel):
    id: int
    sku: str
    name: str
    category: Optional[str] = None
    brand: Optional[str] = None
    active: bool
    created_at: str


class ProductListResponse(BaseModel):
    products: List[ProductResponse]
    total: int
    page: int
    page_size: int


class StatsResponse(BaseModel):
    total_users: int
    total_products: int
    total_watchlist_items: int
    total_alerts: int
    new_users_this_week: int


# ============================================
# Helper Functions
# ============================================

def format_user(user: dict) -> UserResponse:
    return UserResponse(
        id=user['id'],
        email=user['email'],
        full_name=user.get('full_name'),
        role=user.get('role', 'user'),
        is_active=user.get('is_active', True),
        created_at=str(user['created_at']),
        updated_at=str(user['updated_at']) if user.get('updated_at') else None
    )


# ============================================
# Endpoints
# ============================================

@router.get("/stats", response_model=StatsResponse)
async def get_admin_stats(
    admin: TokenPayload = Depends(get_current_admin)
):
    """Get platform statistics"""
    stats = get_stats()
    return StatsResponse(**stats)


@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    admin: TokenPayload = Depends(get_current_admin)
):
    """List all users (admin only)"""
    users, total = UserDB.list_all(page=page, page_size=page_size)
    
    return UserListResponse(
        users=[format_user(u) for u in users],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    admin: TokenPayload = Depends(get_current_admin)
):
    """Get user details"""
    user = UserDB.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return format_user(user)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    admin: TokenPayload = Depends(get_current_admin)
):
    """Update user (role, is_active, full_name)"""
    # Prevent self-demotion
    if int(admin.sub) == user_id and data.role and data.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote yourself"
        )
    
    updates = data.dict(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    user = UserDB.update(user_id, **updates)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return format_user(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    admin: TokenPayload = Depends(get_current_admin)
):
    """Delete user"""
    # Prevent self-deletion
    if int(admin.sub) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    deleted = UserDB.delete(user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@router.get("/watchlist", response_model=WatchlistListResponse)
async def list_all_watchlist(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    admin: TokenPayload = Depends(get_current_admin)
):
    """List all watchlist items across all users"""
    items, total = WatchlistDB.list_all(page=page, page_size=page_size)
    
    return WatchlistListResponse(
        items=[WatchlistItemResponse(
            id=item['id'],
            user_email=item.get('user_email', 'unknown'),
            sku=item['sku'],
            product_name=item.get('product_name'),
            target_price=float(item['target_price']) if item.get('target_price') else None,
            created_at=str(item['created_at'])
        ) for item in items],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/products", response_model=ProductListResponse)
async def list_all_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    admin: TokenPayload = Depends(get_current_admin)
):
    """List all products in the system"""
    products, total = ProductDB.list_all(page=page, page_size=page_size)
    
    return ProductListResponse(
        products=[ProductResponse(
            id=p['id'],
            sku=p['sku'],
            name=p['name'],
            category=p.get('category'),
            brand=p.get('brand'),
            active=p.get('active', True),
            created_at=str(p['created_at'])
        ) for p in products],
        total=total,
        page=page,
        page_size=page_size
    )
