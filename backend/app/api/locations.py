from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.location import (
    UnknownLocationSummary,
    LocationCorrectionRequest,
    BulkLocationCorrectionRequest,
    PaginatedUnknownLocations,
    PaginatedAuditLogs
)
from app.schemas.customer import CustomerOut
from app.services.location_service import LocationService

router = APIRouter(prefix="/locations", tags=["Location Management"])

@router.get("/unknown-summary", response_model=UnknownLocationSummary)
def get_unknown_location_summary(db: Session = Depends(get_db)):
    """Returns exact unique counts for unresolved pincode and district records"""
    return LocationService.get_unknown_summary(db)

@router.get("/unknown-records", response_model=PaginatedUnknownLocations)
def get_unknown_location_records(
    filter_type: Optional[str] = Query("all", description="'all', 'unknown_pincode', 'unknown_district', or 'both'"),
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = "id",
    sort_order: str = "desc",
    db: Session = Depends(get_db)
):
    """Lists customers with missing or unknown location data with filtering and search"""
    return LocationService.get_unknown_records(
        db,
        filter_type=filter_type,
        search=search,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )

@router.put("/correct/{customer_id}", response_model=CustomerOut)
def correct_customer_location(
    customer_id: int,
    req: LocationCorrectionRequest,
    db: Session = Depends(get_db)
):
    """Corrects location for a single customer and writes audit history"""
    try:
        return LocationService.correct_customer_location(db, customer_id, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/bulk-correct")
def bulk_correct_locations(
    req: BulkLocationCorrectionRequest,
    db: Session = Depends(get_db)
):
    """Bulk corrects location fields across selected customer records"""
    try:
        return LocationService.bulk_correct_locations(db, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/audit-history", response_model=PaginatedAuditLogs)
def get_location_audit_history(
    customer_id: Optional[int] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Retrieves chronological location correction audit logs"""
    return LocationService.get_audit_history(
        db,
        customer_id=customer_id,
        search=search,
        page=page,
        page_size=page_size
    )
