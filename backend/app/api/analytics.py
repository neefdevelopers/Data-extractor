from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.analytics import (
    BusinessDashboardKPIs,
    DistrictAnalyticsItem,
    PincodeAnalyticsItem,
    PostOfficeAnalyticsItem,
    GeographicSummaryKPIs
)
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
    post_office: Optional[str] = None,
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

@router.get("/geographic/overview", response_model=GeographicSummaryKPIs)
@router.get("/geographic/summary", response_model=GeographicSummaryKPIs)
def get_geographic_overview(
    preset: Optional[str] = "all",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    employee_id: Optional[int] = None,
    payment_mode: Optional[str] = None,
    product_id: Optional[int] = None,
    district: Optional[str] = None,
    district_id: Optional[int] = None,
    pincode: Optional[str] = None,
    post_office: Optional[str] = None,
    rfm_segment: Optional[str] = None,
    customer_id: Optional[int] = None,
    order_status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return AnalyticsService.get_geographic_overview(
        db,
        preset=preset,
        start_date=start_date,
        end_date=end_date,
        employee_id=employee_id,
        payment_mode=payment_mode,
        product_id=product_id,
        district=district,
        district_id=district_id,
        pincode=pincode,
        post_office=post_office,
        rfm_segment=rfm_segment,
        customer_id=customer_id,
        order_status=order_status,
        search=search
    )

@router.get("/districts", response_model=List[DistrictAnalyticsItem])
@router.get("/geographic/district", response_model=List[DistrictAnalyticsItem])
def get_districts_analytics(
    preset: Optional[str] = "all",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    employee_id: Optional[int] = None,
    payment_mode: Optional[str] = None,
    product_id: Optional[int] = None,
    district: Optional[str] = None,
    district_id: Optional[int] = None,
    pincode: Optional[str] = None,
    post_office: Optional[str] = None,
    rfm_segment: Optional[str] = None,
    customer_id: Optional[int] = None,
    order_status: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = "revenue",
    sort_order: Optional[str] = "desc",
    db: Session = Depends(get_db)
):
    return AnalyticsService.get_district_analytics(
        db,
        preset=preset,
        start_date=start_date,
        end_date=end_date,
        employee_id=employee_id,
        payment_mode=payment_mode,
        product_id=product_id,
        district=district,
        district_id=district_id,
        pincode=pincode,
        post_office=post_office,
        rfm_segment=rfm_segment,
        customer_id=customer_id,
        order_status=order_status,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )

@router.get("/pincodes", response_model=List[PincodeAnalyticsItem])
@router.get("/geographic/pincode", response_model=List[PincodeAnalyticsItem])
def get_pincodes_analytics(
    preset: Optional[str] = "all",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    employee_id: Optional[int] = None,
    payment_mode: Optional[str] = None,
    product_id: Optional[int] = None,
    district: Optional[str] = None,
    district_id: Optional[int] = None,
    pincode: Optional[str] = None,
    post_office: Optional[str] = None,
    rfm_segment: Optional[str] = None,
    customer_id: Optional[int] = None,
    order_status: Optional[str] = None,
    search: Optional[str] = None,
    limit: Optional[int] = None,
    sort_by: Optional[str] = "revenue",
    sort_order: Optional[str] = "desc",
    db: Session = Depends(get_db)
):
    return AnalyticsService.get_pincode_analytics(
        db,
        preset=preset,
        start_date=start_date,
        end_date=end_date,
        employee_id=employee_id,
        payment_mode=payment_mode,
        product_id=product_id,
        district=district,
        district_id=district_id,
        pincode=pincode,
        post_office=post_office,
        rfm_segment=rfm_segment,
        customer_id=customer_id,
        order_status=order_status,
        search=search,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )

@router.get("/geographic/post-office", response_model=List[PostOfficeAnalyticsItem])
def get_post_offices_analytics(
    preset: Optional[str] = "all",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    employee_id: Optional[int] = None,
    payment_mode: Optional[str] = None,
    product_id: Optional[int] = None,
    district: Optional[str] = None,
    district_id: Optional[int] = None,
    pincode: Optional[str] = None,
    post_office: Optional[str] = None,
    rfm_segment: Optional[str] = None,
    customer_id: Optional[int] = None,
    order_status: Optional[str] = None,
    search: Optional[str] = None,
    limit: Optional[int] = None,
    sort_by: Optional[str] = "revenue",
    sort_order: Optional[str] = "desc",
    db: Session = Depends(get_db)
):
    return AnalyticsService.get_post_office_analytics(
        db,
        preset=preset,
        start_date=start_date,
        end_date=end_date,
        employee_id=employee_id,
        payment_mode=payment_mode,
        product_id=product_id,
        district=district,
        district_id=district_id,
        pincode=pincode,
        post_office=post_office,
        rfm_segment=rfm_segment,
        customer_id=customer_id,
        order_status=order_status,
        search=search,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )
