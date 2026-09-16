import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database.session import Base

class RFMScore(Base):
    __tablename__ = "rfm_scores"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    recency_days = Column(Integer, default=0)
    frequency = Column(Integer, default=0)
    monetary_value = Column(Float, default=0.0)
    
    r_score = Column(Integer, default=1)  # 1 to 5
    f_score = Column(Integer, default=1)  # 1 to 5
    m_score = Column(Integer, default=1)  # 1 to 5
    rfm_score = Column(String(10), default="111")  # e.g., "555"
    
    segment = Column(String(100), default="New Customers", index=True)
    calculated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    customer = relationship("Customer", back_populates="rfm_details")

    __table_args__ = (
        Index('idx_rfm_cust', 'customer_id'),
        Index('idx_rfm_seg', 'segment'),
    )

class RFMSegmentRule(Base):
    __tablename__ = "rfm_segments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    segment_name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    color_code = Column(String(30), default="#6366f1")
    
    # Priority for matching if multiple apply
    priority = Column(Integer, default=1)
    
    # Score conditions (JSON string or min/max bounds)
    r_condition = Column(String(50), nullable=True)  # e.g. "4-5" or ">=4"
    f_condition = Column(String(50), nullable=True)  # e.g. "4-5"
    m_condition = Column(String(50), nullable=True)  # e.g. "4-5"
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
