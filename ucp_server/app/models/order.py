"""
Order and checkout data models
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class OrderStatus(str, enum.Enum):
    """Order status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class CheckoutSession(Base):
    """
    Checkout session model for UCP checkout flow
    Stores temporary checkout information before order creation
    """
    __tablename__ = "checkout_sessions"
    
    id = Column(String, primary_key=True)  # UUID
    user_id = Column(String, nullable=False)
    
    # Shipping information
    shipping_name = Column(String, nullable=True)
    shipping_address = Column(Text, nullable=True)
    shipping_city = Column(String, nullable=True)
    shipping_postal_code = Column(String, nullable=True)
    shipping_country = Column(String, default="US")
    
    # Session metadata
    total_amount = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<CheckoutSession(id={self.id}, user_id={self.user_id})>"


class Order(Base):
    """
    Order model
    Created after successful checkout
    """
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String, unique=True, nullable=False, index=True)  # e.g., "ORD-20260212-001"
    user_id = Column(String, nullable=False, index=True)
    
    # Shipping information
    shipping_name = Column(String, nullable=False)
    shipping_address = Column(Text, nullable=False)
    shipping_city = Column(String, nullable=False)
    shipping_postal_code = Column(String, nullable=False)
    shipping_country = Column(String, default="US")
    
    # Order details
    total_amount = Column(Float, nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Order(order_number={self.order_number}, status={self.status})>"


class OrderItem(Base):
    """
    Order item model
    Stores individual products in an order
    """
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    
    # Product information (snapshot at time of order)
    sku = Column(String, nullable=False)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    image_url = Column(String, nullable=True)
    
    # Relationships
    order = relationship("Order", back_populates="items")
    
    def __repr__(self):
        return f"<OrderItem(sku={self.sku}, quantity={self.quantity})>"
    
    @property
    def subtotal(self) -> float:
        """Calculate subtotal for this item"""
        return self.price * self.quantity
