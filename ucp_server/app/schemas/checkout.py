"""
Checkout and session schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CheckoutSessionCreate(BaseModel):
    """Request schema for creating checkout session"""
    # Session will be created from current cart
    pass


class CheckoutSessionUpdate(BaseModel):
    """Request schema for updating checkout session with shipping info"""
    shipping_name: str = Field(..., min_length=1)
    shipping_address: str = Field(..., min_length=1)
    shipping_city: str = Field(..., min_length=1)
    shipping_postal_code: str = Field(..., min_length=1)
    shipping_country: str = "US"
    
    class Config:
        json_schema_extra = {
            "example": {
                "shipping_name": "John Doe",
                "shipping_address": "123 Main St, Apt 4B",
                "shipping_city": "New York",
                "shipping_postal_code": "10001",
                "shipping_country": "US"
            }
        }


class CheckoutSessionResponse(BaseModel):
    """Response schema for checkout session"""
    id: str
    user_id: str
    total_amount: float
    shipping_name: Optional[str] = None
    shipping_address: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_postal_code: Optional[str] = None
    shipping_country: str
    created_at: datetime
    
    class Config:
        from_attributes = True
