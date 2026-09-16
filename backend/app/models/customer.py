import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from app.database.session import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_id_str = Column(String(100), unique=True, index=True, nullable=True)  # External/custom ID if provided
    customer_name = Column(String(255), nullable=False, index=True)
    contact_number = Column(String(30), nullable=True, index=True)
    normalized_contact = Column(String(30), nullable=True, index=True)
    full_address = Column(Text, nullable=True)
    pincode = Column(String(10), nullable=True, index=True)
    post_office = Column(String(255), nullable=True)
    district = Column(String(255), nullable=True, index=True)
    state = Column(String(255), nullable=True)
    
    # Aggregated metrics (recalculated from order data)
    first_order_date = Column(DateTime, nullable=True)
    last_order_date = Column(DateTime, nullable=True)
    total_orders = Column(Integer, default=0)
    total_spend = Column(Float, default=0.0)
    average_order_value = Column(Float, default=0.0)
    
    # RFM summary
    rfm_score = Column(String(10), nullable=True)
    rfm_segment = Column(String(100), nullable=True, index=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")
    rfm_details = relationship("RFMScore", back_populates="customer", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_cust_mobile', 'normalized_contact'),
        Index('idx_cust_pin', 'pincode'),
        Index('idx_cust_district', 'district'),
        Index('idx_cust_segment', 'rfm_segment'),
    )
