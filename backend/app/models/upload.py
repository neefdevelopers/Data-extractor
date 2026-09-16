import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from app.database.session import Base

class UploadBatch(Base):
    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)
    upload_type = Column(String(100), default="COMBINED")  # CUSTOMER, ORDER, PRODUCT, COMBINED
    uploaded_date = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    
    total_rows = Column(Integer, default=0)
    successful_rows = Column(Integer, default=0)
    failed_rows = Column(Integer, default=0)
    duplicate_rows = Column(Integer, default=0)
    updated_rows = Column(Integer, default=0)
    
    new_customers = Column(Integer, default=0)
    new_orders = Column(Integer, default=0)
    new_products = Column(Integer, default=0)
    
    status = Column(String(50), default="UPLOADED", index=True)  # UPLOADED, PROCESSING, COMPLETED, PARTIALLY_COMPLETED, FAILED
    error_message = Column(Text, nullable=True)

    rows = relationship("UploadRow", back_populates="batch", cascade="all, delete-orphan")

class UploadRow(Base):
    __tablename__ = "upload_rows"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    upload_id = Column(Integer, ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False, index=True)
    row_number = Column(Integer, nullable=False)
    status = Column(String(50), default="PENDING")  # SUCCESS, FAILED, DUPLICATE, UPDATED
    raw_data = Column(Text, nullable=True)  # JSON formatted original row
    error_reason = Column(Text, nullable=True)
    suggested_fix = Column(Text, nullable=True)

    batch = relationship("UploadBatch", back_populates="rows")

    __table_args__ = (
        Index('idx_up_row_batch', 'upload_id'),
    )
