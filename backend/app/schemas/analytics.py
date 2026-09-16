from typing import Optional, List
from pydantic import BaseModel

class FilterParams(BaseModel):
    preset: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    employee_id: Optional[int] = None
    payment_mode: Optional[str] = None
    product_id: Optional[int] = None
    district: Optional[str] = None
    pincode: Optional[str] = None
    rfm_segment: Optional[str] = None
    order_status: Optional[str] = None
    search: Optional[str] = None

class DateWiseMetric(BaseModel):
    date: str
    revenue: float
    orders: int
    aov: float

class PaymentModeBreakdown(BaseModel):
    payment_mode: str
    revenue: float
    order_count: int
    percentage_revenue: float
    percentage_orders: float

class BusinessDashboardKPIs(BaseModel):
    total_revenue: float
    total_orders: int
    average_order_value: float
    total_customers: int
    total_products: int
    cod_revenue: float
    prepaid_revenue: float
    cod_orders: int
    prepaid_orders: int
    revenue_trend: List[DateWiseMetric]
    payment_breakdown: List[PaymentModeBreakdown]

class ProductAnalyticsItem(BaseModel):
    product_id: int
    product_name: str
    sku: Optional[str] = None
    category: Optional[str] = None
    total_units_sold: int
    total_orders: int
    total_revenue: float
    avg_revenue_per_order: float
    revenue_contribution_pct: float

class DistrictAnalyticsItem(BaseModel):
    district: str
    state: Optional[str] = None
    customer_count: int
    total_orders: int
    total_revenue: float

class PincodeAnalyticsItem(BaseModel):
    pincode: str
    district: str
    state: Optional[str] = None
    customer_count: int
    total_orders: int
    total_revenue: float

class EmployeeAnalyticsItem(BaseModel):
    employee_id: int
    employee_name: str
    employee_code: Optional[str] = None
    total_orders: int
    total_revenue: float
    average_order_value: float
    customer_count: int
    cod_revenue: float
    prepaid_revenue: float
