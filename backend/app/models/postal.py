import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database.session import Base

class PostalMaster(Base):
    __tablename__ = "postal_master"

    pincode = Column(String(10), primary_key=True, index=True)
    district = Column(String(255), nullable=True, index=True)
    state = Column(String(255), nullable=True, index=True)
    region = Column(String(255), nullable=True)
    division = Column(String(255), nullable=True)
    circle = Column(String(255), nullable=True)
    country = Column(String(50), default="India")
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # 1 PIN -> Multiple Post Offices
    offices = relationship("PostalOffice", back_populates="master", cascade="all, delete-orphan")

class PostalOffice(Base):
    __tablename__ = "postal_offices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pincode = Column(String(10), ForeignKey("postal_master.pincode", ondelete="CASCADE"), nullable=False, index=True)
    office_name = Column(String(255), nullable=False, index=True)
    office_type = Column(String(50), nullable=True)  # Branch Post Office, Sub Post Office, Head Post Office
    delivery_status = Column(String(50), nullable=True)  # Delivery, Non-Delivery
    district = Column(String(255), nullable=True)
    state = Column(String(255), nullable=True)

    master = relationship("PostalMaster", back_populates="offices")
