import datetime
from sqlalchemy import Column, Integer, String, DateTime, Index, func
from sqlalchemy.orm import relationship
from app.database.session import Base

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_name = Column(String(255), nullable=False, index=True)
    employee_code = Column(String(100), unique=True, index=True, nullable=True)
    status = Column(String(50), default="ACTIVE")  # ACTIVE, INACTIVE
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    orders = relationship("Order", back_populates="employee")

    __table_args__ = (
        Index('idx_emp_name_ci', func.lower(func.trim(employee_name))),
    )

