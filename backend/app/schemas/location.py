import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class UnknownLocationSummary(BaseModel):
    unknown_pincode_count: int
    unknown_district_count: int
    both_unknown_count: int
    total_unresolved: int

class UnknownLocationRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id_str: Optional[str] = None
    customer_name: str
    contact_number: Optional[str] = None
    normalized_contact: Optional[str] = None
    full_address: Optional[str] = None
    pincode: Optional[str] = None
    post_office: Optional[str] = None
    source_district: Optional[str] = None
    district_id: Optional[int] = None
    district: Optional[str] = None
    state: Optional[str] = None
    district_resolution_source: Optional[str] = "UNRESOLVED"
    district_status: Optional[str] = "UNRESOLVED"
    unresolved_reason: Optional[str] = None
    total_orders: int = 0
    total_spend: float = 0.0
    missing_type: str  # UNKNOWN_PINCODE, UNKNOWN_DISTRICT, BOTH_UNKNOWN
    source_file_name: Optional[str] = None
    source_row_number: Optional[int] = None
    raw_row_data: Optional[dict] = None
    created_at: datetime.datetime

class LocationCorrectionRequest(BaseModel):
    pincode: Optional[str] = None
    post_office: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    notes: Optional[str] = None
    source: Optional[str] = "MANUAL"

class BulkLocationCorrectionRequest(BaseModel):
    customer_ids: List[int]
    pincode: Optional[str] = None
    post_office: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    notes: Optional[str] = None
    source: Optional[str] = "BULK_UPDATE"

class LocationAuditLog(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    customer_name: Optional[str] = None
    previous_pincode: Optional[str] = None
    new_pincode: Optional[str] = None
    previous_district: Optional[str] = None
    new_district: Optional[str] = None
    previous_post_office: Optional[str] = None
    new_post_office: Optional[str] = None
    previous_state: Optional[str] = None
    new_state: Optional[str] = None
    correction_source: str = "MANUAL"
    changed_by: str = "Admin"
    notes: Optional[str] = None
    created_at: datetime.datetime

class PaginatedUnknownLocations(BaseModel):
    items: List[UnknownLocationRecord]
    total: int
    page: int
    page_size: int
    total_pages: int

class PaginatedAuditLogs(BaseModel):
    items: List[LocationAuditLog]
    total: int
    page: int
    page_size: int
    total_pages: int
