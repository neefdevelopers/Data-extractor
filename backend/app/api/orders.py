from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.order import OrderOut, OrderCreate, OrderUpdate
from app.schemas.common import PaginatedResponse, MessageResponse
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.get("", response_model=PaginatedResponse[OrderOut])
def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    product_id: Optional[int] = None,
    payment_mode: Optional[str] = None,
    order_status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "order_date",
    sort_order: str = "desc",
    db: Session = Depends(get_db)
):
    items, total = OrderService.get_orders(
        db, page=page, page_size=page_size, customer_id=customer_id,
        employee_id=employee_id, product_id=product_id, payment_mode=payment_mode,
        order_status=order_status, start_date=start_date, end_date=end_date,
        search=search, sort_by=sort_by, sort_order=sort_order
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = OrderService.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
