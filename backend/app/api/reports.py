import os
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.export_service import ExportService

router = APIRouter(prefix="/reports", tags=["Reports & Exports"])

@router.get("/customers")
def export_customers(
    format: str = Query("xlsx", regex="^(xlsx|csv)$"),
    search: Optional[str] = None,
    district: Optional[str] = None,
    post_office: Optional[str] = None,
    pincode: Optional[str] = None,
    rfm_segment: Optional[str] = None,
    min_orders: Optional[int] = None,
    max_orders: Optional[int] = None,
    min_spend: Optional[float] = None,
    max_spend: Optional[float] = None,
    sort_by: str = "total_spend",
    sort_order: str = "desc",
    db: Session = Depends(get_db)
):
    filepath = ExportService.export_customers(
        db,
        format_type=format,
        search=search,
        district=district,
        post_office=post_office,
        pincode=pincode,
        rfm_segment=rfm_segment,
        min_orders=min_orders,
        max_orders=max_orders,
        min_spend=min_spend,
        max_spend=max_spend,
        sort_by=sort_by,
        sort_order=sort_order
    )
    filename = os.path.basename(filepath)
    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == "xlsx" else "text/csv"
    return FileResponse(path=filepath, filename=filename, media_type=media_type)

@router.get("/orders")
def export_orders(
    format: str = Query("xlsx", regex="^(xlsx|csv)$"),
    payment_mode: Optional[str] = None,
    order_status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    filepath = ExportService.export_orders(db, format_type=format, payment_mode=payment_mode, order_status=order_status, start_date=start_date, end_date=end_date)
    filename = os.path.basename(filepath)
    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == "xlsx" else "text/csv"
    return FileResponse(path=filepath, filename=filename, media_type=media_type)

@router.get("/rfm")
def export_rfm(
    format: str = Query("xlsx", regex="^(xlsx|csv)$"),
    db: Session = Depends(get_db)
):
    filepath = ExportService.export_rfm(db, format_type=format)
    filename = os.path.basename(filepath)
    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == "xlsx" else "text/csv"
    return FileResponse(path=filepath, filename=filename, media_type=media_type)

@router.get("/geographic")
def export_geographic(
    format: str = Query("xlsx", regex="^(xlsx|csv)$"),
    db: Session = Depends(get_db)
):
    filepath = ExportService.export_geographic(db, format_type=format)
    filename = os.path.basename(filepath)
    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == "xlsx" else "text/csv"
    return FileResponse(path=filepath, filename=filename, media_type=media_type)

@router.get("/products")
def export_products(
    format: str = Query("xlsx", regex="^(xlsx|csv)$"),
    db: Session = Depends(get_db)
):
    filepath = ExportService.export_products(db, format_type=format)
    filename = os.path.basename(filepath)
    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == "xlsx" else "text/csv"
    return FileResponse(path=filepath, filename=filename, media_type=media_type)

@router.get("/employees")
def export_employees(
    format: str = Query("xlsx", regex="^(xlsx|csv)$"),
    db: Session = Depends(get_db)
):
    filepath = ExportService.export_employees(db, format_type=format)
    filename = os.path.basename(filepath)
    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == "xlsx" else "text/csv"
    return FileResponse(path=filepath, filename=filename, media_type=media_type)
