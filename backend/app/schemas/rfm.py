from typing import List, Dict
from pydantic import BaseModel

class RFMSegmentSummary(BaseModel):
    segment_name: str
    customer_count: int
    percentage: float
    total_revenue: float
    avg_monetary: float
    avg_frequency: float
    avg_recency_days: float
    color_code: str

class ScoreDistribution(BaseModel):
    score: int
    customer_count: int

class RFMDashboardResponse(BaseModel):
    total_customers_with_rfm: int
    customers_without_sufficient_data: int
    avg_recency_days: float
    avg_frequency: float
    avg_monetary: float
    segments: List[RFMSegmentSummary]
    recency_distribution: List[ScoreDistribution]
    frequency_distribution: List[ScoreDistribution]
    monetary_distribution: List[ScoreDistribution]
