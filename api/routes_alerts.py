"""
Price Alerts API Routes for Noon-E-Commerce
Phase 8: Alert management, notifications, mark as read
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel

from auth import get_current_user, TokenPayload
from db_postgres import PriceAlertDB

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


# ============================================
# Pydantic Models
# ============================================

class AlertResponse(BaseModel):
    """Single alert response"""
    id: int
    sku: str
    old_price: float
    new_price: float
    change_pct: float
    alert_type: str
    read_at: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    """Paginated alert list"""
    items: List[AlertResponse]
    total: int
    unread_count: int
    page: int
    page_size: int


class AlertMarkReadRequest(BaseModel):
    """Mark alerts as read"""
    alert_ids: List[int]


class AlertMarkReadResponse(BaseModel):
    """Mark read response"""
    marked: int


# ============================================
# Helper Functions
# ============================================

def format_alert(alert: dict) -> AlertResponse:
    """Format alert dict as response"""
    old_price = float(alert['old_price'])
    new_price = float(alert['new_price'])
    change_pct = ((new_price - old_price) / old_price * 100) if old_price > 0 else 0
    
    # DB uses 'sent_at' instead of 'created_at'
    created_at = alert.get('created_at') or alert.get('sent_at')
    
    return AlertResponse(
        id=alert['id'],
        sku=alert['sku'],
        old_price=old_price,
        new_price=new_price,
        change_pct=round(change_pct, 2),
        alert_type=alert['alert_type'],
        read_at=str(alert['read_at']) if alert.get('read_at') else None,
        created_at=str(created_at) if created_at else ''
    )


# ============================================
# Endpoints
# ============================================

@router.get("", response_model=AlertListResponse)
async def list_alerts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    unread_only: bool = Query(default=False, description="Show only unread alerts"),
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    List price alerts for current user.
    
    - **page**: Page number
    - **page_size**: Items per page
    - **unread_only**: Filter to unread alerts only
    """
    user_id = int(current_user.sub)
    
    items, total = PriceAlertDB.list_by_user(
        user_id=user_id,
        page=page,
        page_size=page_size,
        unread_only=unread_only
    )
    
    # Get unread count
    _, unread_total = PriceAlertDB.list_by_user(
        user_id=user_id,
        page=1,
        page_size=1,
        unread_only=True
    )
    
    return AlertListResponse(
        items=[format_alert(a) for a in items],
        total=total,
        unread_count=unread_total,
        page=page,
        page_size=page_size
    )


@router.get("/unread-count")
async def get_unread_count(
    current_user: TokenPayload = Depends(get_current_user)
):
    """Get count of unread alerts"""
    user_id = int(current_user.sub)
    
    _, count = PriceAlertDB.list_by_user(
        user_id=user_id,
        page=1,
        page_size=1,
        unread_only=True
    )
    
    return {"unread_count": count}


@router.post("/{alert_id}/read", status_code=status.HTTP_200_OK)
async def mark_alert_read(
    alert_id: int,
    current_user: TokenPayload = Depends(get_current_user)
):
    """Mark a single alert as read"""
    user_id = int(current_user.sub)
    
    success = PriceAlertDB.mark_read(alert_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    return {"success": True, "alert_id": alert_id}


@router.post("/mark-read", response_model=AlertMarkReadResponse)
async def mark_alerts_read(
    data: AlertMarkReadRequest,
    current_user: TokenPayload = Depends(get_current_user)
):
    """Mark multiple alerts as read"""
    user_id = int(current_user.sub)
    
    marked = 0
    for alert_id in data.alert_ids:
        if PriceAlertDB.mark_read(alert_id, user_id):
            marked += 1
    
    return AlertMarkReadResponse(marked=marked)


@router.post("/mark-all-read")
async def mark_all_read(
    current_user: TokenPayload = Depends(get_current_user)
):
    """Mark all alerts as read for current user"""
    user_id = int(current_user.sub)
    
    # Get all unread alerts
    items, _ = PriceAlertDB.list_by_user(
        user_id=user_id,
        page=1,
        page_size=1000,
        unread_only=True
    )
    
    marked = 0
    for alert in items:
        if PriceAlertDB.mark_read(alert['id'], user_id):
            marked += 1
    
    return {"success": True, "marked": marked}
