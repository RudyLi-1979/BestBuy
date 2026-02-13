"""
Cart data models
Based on Android App's CartItem.kt and CartRepository.kt
"""
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base


class CartItem(Base):
    """
    Shopping cart item model
    Mirrors the Android App's CartItem data class
    """
    __tablename__ = "cart_items"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)  # Guest user ID or authenticated user ID
    sku = Column(String, nullable=False)  # Product SKU from Best Buy API
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    image_url = Column(String, nullable=True)
    quantity = Column(Integer, default=1, nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<CartItem(sku={self.sku}, name={self.name}, quantity={self.quantity})>"
    
    @property
    def subtotal(self) -> float:
        """Calculate subtotal for this item"""
        return self.price * self.quantity
