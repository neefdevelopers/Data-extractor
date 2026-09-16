from typing import Dict, Any, List
from pydantic import BaseModel

class RevenueSettings(BaseModel):
    delivered_eligible: bool = True
    completed_eligible: bool = True
    cancelled_eligible: bool = False
    returned_eligible: bool = False
    refunded_eligible: bool = False
    pending_eligible: bool = False

class RFMSettings(BaseModel):
    # Quantile thresholds or custom limits
    recency_weight: float = 0.33
    frequency_weight: float = 0.33
    monetary_weight: float = 0.34

class SystemSettingsOut(BaseModel):
    revenue_rules: RevenueSettings
    rfm_settings: RFMSettings
    postal_api_url: str
    database_url_masked: str
    app_version: str = "1.0.0"
