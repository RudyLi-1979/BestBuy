"""
Chat schemas for Gemini LLM integration
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.schemas.product import ProductSimple


class ChatMessage(BaseModel):
    """Single chat message"""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "I'm looking for a new iPhone"
            }
        }


class ChatRequest(BaseModel):
    """Chat request from user"""
    message: str = Field(..., description="User's message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "I want to buy an iPhone 15 Pro",
                "session_id": "abc123"
            }
        }


class FunctionCall(BaseModel):
    """Function call from Gemini"""
    name: str = Field(..., description="Function name")
    arguments: Dict[str, Any] = Field(..., description="Function arguments")


class ChatResponse(BaseModel):
    """Chat response to user"""
    message: str = Field(..., description="Assistant's response message")
    session_id: str = Field(..., description="Session ID")
    function_calls: Optional[List[FunctionCall]] = Field(None, description="Function calls made by AI")
    products: Optional[List[ProductSimple]] = Field(None, description="Product recommendations to display in the chat")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "I found several iPhone 15 Pro models. Here are the top options...",
                "session_id": "abc123",
                "function_calls": [
                    {
                        "name": "search_products",
                        "arguments": {"query": "iPhone 15 Pro", "max_results": 5}
                    }
                ],
                "products": [
                    {
                        "sku": 1234567,
                        "name": "iPhone 15 Pro 256GB",
                        "sale_price": 999.0,
                        "regular_price": 1099.0,
                        "on_sale": True,
                        "manufacturer": "Apple",
                        "image": "https://example.com/image.jpg"
                    }
                ]
            }
        }
