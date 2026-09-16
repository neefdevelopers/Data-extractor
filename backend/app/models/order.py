import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database.session import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_number = Column(String(100), unique=True, index=True, nullable=False)  # Order ID / Invoice No
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    order_date = Column(DateTime, nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True)
    
    payment_mode = Column(String(50), default="COD", index=True)  # COD, PREPAID, etc.
    order_status = Column(String(50), default="DELIVERED", index=True)  # DELIVERED, COMPLETED, CANCELLED, RETURNED, REFUNDED, PENDING
    
    subtotal = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    shipping_charge = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    revenue_amount = Column(Float, default=0.0)  # Calculated based on RevenueService eligibility rules
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="orders")
    employee = relationship("Employee", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_ord_cust', 'customer_id'),
        Index('idx_ord_date', 'order_date'),
        Index('idx_ord_emp', 'employee_id'),
        Index('idx_ord_paymode', 'payment_mode'),
        Index('idx_ord_status', 'order_status'),
    )
