from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ColumnMapping(BaseModel):
    # standard target field -> source file header name
    customer_name: Optional[str] = None
    contact_number: Optional[str] = None
    full_address: Optional[str] = None
    pincode: Optional[str] = None
    post_office: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    
    order_number: Optional[str] = None
    order_date: Optional[str] = None
    payment_mode: Optional[str] = None
    order_status: Optional[str] = None
    total_amount: Optional[str] = None
    employee_name: Optional[str] = None
    
    product_name: Optional[str] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    price: Optional[str] = None
    quantity: Optional[str] = None

class FileAnalysisResponse(BaseModel):
    file_name: str
    temp_file_id: str
    total_rows: int
    detected_columns: List[str]
    suggested_import_type: str  # CUSTOMER, ORDER, PRODUCT, COMBINED
    auto_mappings: Dict[str, Optional[str]]
    sample_rows: List[Dict[str, Any]]
    validation_warnings: List[str] = []

class ImportConfirmRequest(BaseModel):
    temp_file_id: str
    file_name: str
    import_type: str  # CUSTOMER, ORDER, PRODUCT, COMBINED
    column_mapping: Dict[str, Optional[str]]
    update_existing: bool = True

class UploadRowOut(BaseModel):
    id: int
    row_number: int
    status: str
    raw_data: Optional[str] = None
    error_reason: Optional[str] = None
    suggested_fix: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class UploadBatchOut(BaseModel):
    id: int
    file_name: str
    upload_type: str
    uploaded_date: datetime
    total_rows: int
    successful_rows: int
    failed_rows: int
    duplicate_rows: int
    updated_rows: int
    new_customers: int
    new_orders: int
    new_products: int
    status: str
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class UploadBatchDetail(UploadBatchOut):
    failed_row_items: List[UploadRowOut] = []
