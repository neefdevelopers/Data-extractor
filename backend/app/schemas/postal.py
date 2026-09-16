from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class PostalOfficeOut(BaseModel):
    id: int
    pincode: str
    office_name: str
    office_type: Optional[str] = None
    delivery_status: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class PostalMasterOut(BaseModel):
    pincode: str
    district: Optional[str] = None
    state: Optional[str] = None
    region: Optional[str] = None
    division: Optional[str] = None
    circle: Optional[str] = None
    country: str = "India"
    offices: List[PostalOfficeOut] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class PostalLookupResult(BaseModel):
    pincode: str
    is_valid: bool
    is_cached: bool
    district: Optional[str] = None
    state: Optional[str] = None
    region: Optional[str] = None
    offices: List[str] = []
    error_message: Optional[str] = None
