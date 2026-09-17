from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.customer import CustomerOut, CustomerDetail, CustomerCreate, CustomerUpdate
from app.schemas.order import OrderOut
from app.schemas.common import PaginatedResponse, MessageResponse
from app.services.customer_service import CustomerService
from app.services.order_service import OrderService

router = APIRouter(prefix="/customers", tags=["Customers"])

@router.get("", response_model=PaginatedResponse[CustomerOut])
def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    district: Optional[str] = None,
    post_office: Optional[str] = None,
    pincode: Optional[str] = None,
    rfm_segment: Optional[str] = None,
    min_orders: Optional[int] = None,
    max_orders: Optional[int] = None,
    min_spend: Optional[float] = None,
    max_spend: Optional[float] = None,
    sort_by: str = "id",
    sort_order: str = "desc",
    db: Session = Depends(get_db)
):
    items, total = CustomerService.get_customers(
        db, page, page_size, search, district, post_office, pincode, rfm_segment,
        min_orders, max_orders, min_spend, max_spend, sort_by, sort_order
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/{customer_id}", response_model=CustomerDetail)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    cust = CustomerService.get_customer_by_id(db, customer_id)
    if not cust:
        raise HTTPException(status_code=404, detail="Customer not found")
    return cust

@router.post("", response_model=CustomerOut)
def create_customer(
    data: CustomerCreate,
    db: Session = Depends(get_db)
):
    """Creates a new customer with automatic Pincode-first district resolution"""
    try:
        return CustomerService.create_customer(db, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{customer_id}", response_model=CustomerDetail)
def update_customer(
    customer_id: int,
    data: CustomerUpdate,
    db: Session = Depends(get_db)
):
    """Updates customer details with automatic Pincode-first district resolution"""
    try:
        CustomerService.update_customer(db, customer_id, data)
        updated_cust = CustomerService.get_customer_by_id(db, customer_id)
        if not updated_cust:
            raise HTTPException(status_code=404, detail="Customer not found")
        return updated_cust
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{customer_id}/orders", response_model=PaginatedResponse[OrderOut])
def get_customer_orders(
    customer_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    items, total = OrderService.get_orders(db, page=page, page_size=page_size, customer_id=customer_id)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

