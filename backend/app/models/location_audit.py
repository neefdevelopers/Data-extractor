import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from app.database.session import Base

class LocationCorrectionAudit(Base):
    __tablename__ = "location_correction_audits"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Previous location state
    previous_pincode = Column(String(20), nullable=True)
    previous_district = Column(String(255), nullable=True)
    previous_post_office = Column(String(255), nullable=True)
    previous_state = Column(String(255), nullable=True)
    
    # New corrected location state
    new_pincode = Column(String(20), nullable=True)
    new_district = Column(String(255), nullable=True)
    new_post_office = Column(String(255), nullable=True)
    new_state = Column(String(255), nullable=True)
    
    # Metadata
    correction_source = Column(String(50), default="MANUAL")  # MANUAL, POSTAL_API, BULK_UPDATE
    changed_by = Column(String(100), default="Admin")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    # Relationships
    customer = relationship("Customer", backref="location_audits")

    __table_args__ = (
        Index('idx_loc_audit_cust', 'customer_id'),
        Index('idx_loc_audit_created', 'created_at'),
    )
