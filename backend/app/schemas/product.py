from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ProductBase(BaseModel):
    product_name: str
    sku: Optional[str] = None
    category: Optional[str] = None
    price: float = 0.0

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None

class ProductOut(ProductBase):
    id: int
    total_units_sold: int = 0
    total_orders: int = 0
    total_revenue: float = 0.0
    avg_revenue_per_order: float = 0.0
    revenue_contribution_pct: float = 0.0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
