import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.orm import relationship
from app.database.session import Base

class DistrictMaster(Base):
    __tablename__ = "district_master"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    canonical_name = Column(String(255), nullable=False)  # e.g. "Malappuram"
    state = Column(String(255), default="Kerala", nullable=False)
    normalized_key = Column(String(255), unique=True, index=True, nullable=False)  # e.g. "malappuram"
    aliases = Column(Text, nullable=True)  # JSON/comma-separated known aliases
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    customers = relationship("Customer", back_populates="district_master", foreign_keys="Customer.district_id")

    __table_args__ = (
        Index('idx_district_norm_key', 'normalized_key', unique=True),
        Index('idx_district_canonical', 'canonical_name'),
    )
