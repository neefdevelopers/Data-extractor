from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from app.models.data_quality import DataQualityIssue
from app.models.customer import Customer
from app.models.order import Order
from app.models.product import Product

class DataQualityService:
    @staticmethod
    def log_issue(
        db: Session,
        entity_type: str,
        entity_id: Optional[str],
        field_name: str,
        issue_type: str,
        raw_value: Optional[str],
        message: str,
        suggested_fix: Optional[str] = None,
        row_number: Optional[int] = None,
        batch_id: Optional[int] = None,
        auto_commit: bool = False
    ) -> DataQualityIssue:
        issue = DataQualityIssue(
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            row_number=row_number,
            batch_id=batch_id,
            field_name=field_name,
            issue_type=issue_type,
            raw_value=str(raw_value) if raw_value is not None else None,
            message=message,
            suggested_fix=suggested_fix,
            is_resolved=False
        )
        db.add(issue)
        if auto_commit:
            db.commit()
            db.refresh(issue)
        else:
            db.flush()
        return issue

    @staticmethod
    def get_issues(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        issue_type: Optional[str] = None,
        entity_type: Optional[str] = None,
        is_resolved: Optional[bool] = None,
        batch_id: Optional[int] = None
    ) -> Tuple[List[DataQualityIssue], int]:
        query = db.query(DataQualityIssue)
        if issue_type:
            query = query.filter(DataQualityIssue.issue_type == issue_type)
        if entity_type:
            query = query.filter(DataQualityIssue.entity_type == entity_type)
        if is_resolved is not None:
            query = query.filter(DataQualityIssue.is_resolved == is_resolved)
        if batch_id:
            query = query.filter(DataQualityIssue.batch_id == batch_id)

        total = query.count()
        items = query.order_by(desc(DataQualityIssue.created_at)).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    @staticmethod
    def get_summary(db: Session) -> Dict[str, Any]:
        total = db.query(DataQualityIssue).count()
        unresolved = db.query(DataQualityIssue).filter(DataQualityIssue.is_resolved == False).count()
        resolved = total - unresolved

        by_type_rows = db.query(
            DataQualityIssue.issue_type,
            func.count(DataQualityIssue.id)
        ).filter(DataQualityIssue.is_resolved == False).group_by(DataQualityIssue.issue_type).all()
        
        by_type = {row[0]: row[1] for row in by_type_rows}

        by_entity_rows = db.query(
            DataQualityIssue.entity_type,
            func.count(DataQualityIssue.id)
        ).filter(DataQualityIssue.is_resolved == False).group_by(DataQualityIssue.entity_type).all()

        by_entity = {row[0]: row[1] for row in by_entity_rows}

        return {
            "total_issues": total,
            "unresolved_issues": unresolved,
            "resolved_issues": resolved,
            "by_type": by_type,
            "by_entity": by_entity
        }

    @staticmethod
    def resolve_issue(db: Session, issue_id: int) -> bool:
        issue = db.query(DataQualityIssue).filter(DataQualityIssue.id == issue_id).first()
        if not issue:
            return False
        issue.is_resolved = True
        db.commit()
        return True
