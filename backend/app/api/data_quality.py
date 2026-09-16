import os
import pandas as pd
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.data_quality import DataQualityIssueOut, DataQualitySummary
from app.schemas.common import PaginatedResponse, MessageResponse
from app.models.data_quality import DataQualityIssue
from app.services.data_quality_service import DataQualityService

router = APIRouter(prefix="/data-quality", tags=["Data Quality"])

@router.get("/summary", response_model=DataQualitySummary)
def get_data_quality_summary(db: Session = Depends(get_db)):
    return DataQualityService.get_summary(db)

@router.get("/issues", response_model=PaginatedResponse[DataQualityIssueOut])
def list_data_quality_issues(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    issue_type: Optional[str] = None,
    entity_type: Optional[str] = None,
    is_resolved: Optional[bool] = None,
    batch_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    items, total = DataQualityService.get_issues(
        db, page=page, page_size=page_size, issue_type=issue_type,
        entity_type=entity_type, is_resolved=is_resolved, batch_id=batch_id
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.post("/issues/{issue_id}/resolve", response_model=MessageResponse)
def resolve_issue(issue_id: int, db: Session = Depends(get_db)):
    success = DataQualityService.resolve_issue(db, issue_id)
    if not success:
        raise HTTPException(status_code=404, detail="Issue not found")
    return MessageResponse(success=True, message="Issue marked as resolved")

@router.get("/export")
def export_data_quality_issues(db: Session = Depends(get_db)):
    issues = db.query(DataQualityIssue).filter(DataQualityIssue.is_resolved == False).all()
    data = []
    for iss in issues:
        data.append({
            "Issue ID": iss.id,
            "Entity Type": iss.entity_type,
            "Entity ID": iss.entity_id or "",
            "Field Name": iss.field_name,
            "Issue Type": iss.issue_type,
            "Raw Value": iss.raw_value or "",
            "Message": iss.message,
            "Suggested Fix": iss.suggested_fix or "",
            "Logged At": iss.created_at.strftime("%Y-%m-%d %H:%M:%S") if iss.created_at else ""
        })
    df = pd.DataFrame(data) if data else pd.DataFrame(columns=["Issue ID", "Entity Type", "Issue Type", "Message"])
    export_dir = os.getenv("EXPORT_DIR", "../exports")
    os.makedirs(export_dir, exist_ok=True)
    filepath = os.path.join(export_dir, "data_quality_issues.csv")
    df.to_csv(filepath, index=False)
    return FileResponse(path=filepath, filename="data_quality_issues.csv", media_type="text/csv")
