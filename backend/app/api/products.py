from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.product import ProductOut
from app.schemas.common import PaginatedResponse
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("", response_model=PaginatedResponse[ProductOut])
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    sort_by: str = "total_revenue",
    sort_order: str = "desc",
    db: Session = Depends(get_db)
):
    items, total = ProductService.get_products_analytics(
        db, page=page, page_size=page_size, search=search,
        category=category, sort_by=sort_by, sort_order=sort_order
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
