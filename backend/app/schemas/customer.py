from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class CustomerBase(BaseModel):
    customer_id_str: Optional[str] = None
    customer_name: str
    contact_number: Optional[str] = None
    normalized_contact: Optional[str] = None
    full_address: Optional[str] = None
    pincode: Optional[str] = None
    post_office: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    customer_name: Optional[str] = None
    contact_number: Optional[str] = None
    full_address: Optional[str] = None
    pincode: Optional[str] = None
    post_office: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None

class CustomerRFMInfo(BaseModel):
    recency_days: int
    frequency: int
    monetary_value: float
    r_score: int
    f_score: int
    m_score: int
    rfm_score: str
    segment: str

class CustomerProductSummary(BaseModel):
    product_name: str
    sku: Optional[str] = None
    category: Optional[str] = None
    total_quantity: int = 0
    total_spend: float = 0.0
    last_purchased_date: Optional[datetime] = None

class CustomerOut(CustomerBase):
    id: int
    first_order_date: Optional[datetime] = None
    last_order_date: Optional[datetime] = None
    total_orders: int = 0
    total_spend: float = 0.0
    average_order_value: float = 0.0
    rfm_score: Optional[str] = None
    rfm_segment: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CustomerDetail(CustomerOut):
    rfm_details: Optional[CustomerRFMInfo] = None
    formatted_clipboard_text: Optional[str] = None
    purchased_products: List[CustomerProductSummary] = []
