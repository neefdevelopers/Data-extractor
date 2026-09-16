from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class OrderItemBase(BaseModel):
    product_id: Optional[int] = None
    product_name: str
    quantity: int = 1
    unit_price: float = 0.0
    discount: float = 0.0
    item_total: float = 0.0

class OrderItemOut(OrderItemBase):
    id: int
    order_id: int

    model_config = ConfigDict(from_attributes=True)

class OrderBase(BaseModel):
    order_number: str
    customer_id: int
    order_date: datetime
    employee_id: Optional[int] = None
    payment_mode: str = "COD"
    order_status: str = "DELIVERED"
    subtotal: float = 0.0
    discount: float = 0.0
    shipping_charge: float = 0.0
    tax: float = 0.0
    total_amount: float = 0.0
    revenue_amount: float = 0.0

class OrderCreate(BaseModel):
    order_number: str
    customer_id: int
    order_date: datetime
    employee_id: Optional[int] = None
    payment_mode: str = "COD"
    order_status: str = "DELIVERED"
    subtotal: Optional[float] = 0.0
    discount: Optional[float] = 0.0
    shipping_charge: Optional[float] = 0.0
    tax: Optional[float] = 0.0
    total_amount: float
    items: Optional[List[OrderItemBase]] = []

class OrderUpdate(BaseModel):
    employee_id: Optional[int] = None
    payment_mode: Optional[str] = None
    order_status: Optional[str] = None
    subtotal: Optional[float] = None
    discount: Optional[float] = None
    shipping_charge: Optional[float] = None
    tax: Optional[float] = None
    total_amount: Optional[float] = None

class OrderOut(OrderBase):
    id: int
    customer_name: Optional[str] = None
    customer_contact: Optional[str] = None
    customer_district: Optional[str] = None
    customer_pincode: Optional[str] = None
    employee_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemOut] = []

    model_config = ConfigDict(from_attributes=True)
