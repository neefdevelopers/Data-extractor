from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.analytics import BusinessDashboardKPIs, DistrictAnalyticsItem, PincodeAnalyticsItem
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/dashboard", response_model=BusinessDashboardKPIs)
def get_business_dashboard_kpis(
    preset: Optional[str] = "all",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    employee_id: Optional[int] = None,
    payment_mode: Optional[str] = None,
    product_id: Optional[int] = None,
    district: Optional[str] = None,
    pincode: Optional[str] = None,
    rfm_segment: Optional[str] = None,
    customer_id: Optional[int] = None,
    order_status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return AnalyticsService.get_business_dashboard(
        db,
        preset=preset,
        start_date=start_date,
        end_date=end_date,
        employee_id=employee_id,
        payment_mode=payment_mode,
        product_id=product_id,
        district=district,
        pincode=pincode,
        rfm_segment=rfm_segment,
        customer_id=customer_id,
        order_status=order_status,
        search=search
    )

@router.get("/districts", response_model=List[DistrictAnalyticsItem])
def get_districts_analytics(search: Optional[str] = None, db: Session = Depends(get_db)):
    return AnalyticsService.get_district_analytics(db, search=search)

@router.get("/pincodes", response_model=List[PincodeAnalyticsItem])
def get_pincodes_analytics(
    district: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return AnalyticsService.get_pincode_analytics(db, district=district, search=search)
