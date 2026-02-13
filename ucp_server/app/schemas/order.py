"""
Order schemas
"""
from pydantic import BaseModel
from typing import List
from datetime import datetime
from app.models.order import OrderStatus


class OrderItemResponse(BaseModel):
    """Response schema for order item"""
    id: int
    sku: str
    name: str
    price: float
    quantity: int
    subtotal: float
    image_url: str | None = None
    
    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    """Internal schema for creating order from checkout session"""
    # This is used internally, not exposed to API
    pass


class OrderResponse(BaseModel):
    """Response schema for order"""
    id: int
    order_number: str
    user_id: str
    shipping_name: str
    shipping_address: str
    shipping_city: str
    shipping_postal_code: str
    shipping_country: str
    total_amount: float
    status: OrderStatus
    items: List[OrderItemResponse]
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "order_number": "ORD-20260212-001",
                "user_id": "guest_abc123",
                "shipping_name": "John Doe",
                "shipping_address": "123 Main St",
                "shipping_city": "New York",
                "shipping_postal_code": "10001",
                "total_amount": 999.99,
                "status": "confirmed",
                "items": [
                    {
                        "sku": "6428324",
                        "name": "iPhone 15 Pro",
                        "price": 999.99,
                        "quantity": 1,
                        "subtotal": 999.99
                    }
                ]
            }
        }
