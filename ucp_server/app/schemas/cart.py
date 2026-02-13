"""
Cart schemas for API requests and responses
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class CartItemCreate(BaseModel):
    """Request schema for adding item to cart"""
    sku: str
    name: str
    price: float
    image_url: Optional[str] = None
    quantity: int = 1
    
    class Config:
        json_schema_extra = {
            "example": {
                "sku": "6428324",
                "name": "Apple - iPhone 15 Pro 128GB",
                "price": 999.99,
                "quantity": 1
            }
        }


class CartItemResponse(BaseModel):
    """Response schema for cart item"""
    id: int
    user_id: str
    sku: str
    name: str
    price: float
    image_url: Optional[str] = None
    quantity: int
    subtotal: float
    added_at: datetime
    
    class Config:
        from_attributes = True  # Enable ORM mode


class CartResponse(BaseModel):
    """Response schema for cart with all items"""
    items: List[CartItemResponse]
    total_price: float
    item_count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "id": 1,
                        "sku": "6428324",
                        "name": "Apple - iPhone 15 Pro 128GB",
                        "price": 999.99,
                        "quantity": 1,
                        "subtotal": 999.99
                    }
                ],
                "total_price": 999.99,
                "item_count": 1
            }
        }


class CartItemUpdate(BaseModel):
    """Request schema for updating cart item quantity"""
    quantity: int = Field(ge=0, description="Quantity (0 to remove item)")
