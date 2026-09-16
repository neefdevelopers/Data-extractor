from sqlalchemy import Column, Integer, String, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database.session import Base

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    product_name = Column(String(255), nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    item_total = Column(Float, default=0.0)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

    __table_args__ = (
        Index('idx_item_ord', 'order_id'),
        Index('idx_item_prod', 'product_id'),
    )
