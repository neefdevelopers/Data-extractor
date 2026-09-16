import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Index
from app.database.session import Base

class DataQualityIssue(Base):
    __tablename__ = "data_quality_issues"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False, index=True)  # CUSTOMER, ORDER, PRODUCT, POSTAL
    entity_id = Column(String(100), nullable=True, index=True)
    row_number = Column(Integer, nullable=True)
    batch_id = Column(Integer, nullable=True, index=True)
    
    field_name = Column(String(100), nullable=False)
    issue_type = Column(String(100), nullable=False, index=True)  
    # MISSING_NAME, INVALID_CONTACT, MISSING_PIN, INVALID_PIN, POSTAL_CONFLICT, DUPLICATE_CUSTOMER, 
    # MISSING_ORDER_ID, DUPLICATE_ORDER, INVALID_DATE, INVALID_AMOUNT, INVALID_PAYMENT_MODE, INVALID_ORDER_STATUS
    
    raw_value = Column(Text, nullable=True)
    message = Column(Text, nullable=False)
    suggested_fix = Column(Text, nullable=True)
    is_resolved = Column(Boolean, default=False, index=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_dq_type', 'issue_type'),
        Index('idx_dq_entity', 'entity_type', 'entity_id'),
        Index('idx_dq_resolved', 'is_resolved'),
    )
