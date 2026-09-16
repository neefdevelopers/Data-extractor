import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from app.database.session import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_name = Column(String(255), nullable=False, index=True)
    sku = Column(String(100), unique=True, index=True, nullable=True)
    category = Column(String(100), nullable=True, index=True)
    price = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    order_items = relationship("OrderItem", back_populates="product")
