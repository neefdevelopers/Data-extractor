from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class DataQualityIssueOut(BaseModel):
    id: int
    entity_type: str
    entity_id: Optional[str] = None
    row_number: Optional[int] = None
    batch_id: Optional[int] = None
    field_name: str
    issue_type: str
    raw_value: Optional[str] = None
    message: str
    suggested_fix: Optional[str] = None
    is_resolved: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DataQualitySummary(BaseModel):
    total_issues: int
    unresolved_issues: int
    resolved_issues: int
    by_type: Dict[str, int]
    by_entity: Dict[str, int]
