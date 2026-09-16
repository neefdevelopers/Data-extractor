from typing import Optional, List, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

class MessageResponse(BaseModel):
    success: bool
    message: str
    details: Optional[dict] = None

class DateRangeFilter(BaseModel):
    preset: Optional[str] = None  # today, yesterday, last7days, last30days, thisMonth, prevMonth, custom
    start_date: Optional[str] = None  # YYYY-MM-DD
    end_date: Optional[str] = None    # YYYY-MM-DD
