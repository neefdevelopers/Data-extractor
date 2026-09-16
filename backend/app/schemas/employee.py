from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class EmployeeBase(BaseModel):
    employee_name: str
    employee_code: Optional[str] = None
    status: str = "ACTIVE"

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    status: Optional[str] = None

class EmployeeOut(EmployeeBase):
    id: int
    total_orders: int = 0
    total_revenue: float = 0.0
    average_order_value: float = 0.0
    customer_count: int = 0
    cod_revenue: float = 0.0
    prepaid_revenue: float = 0.0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
