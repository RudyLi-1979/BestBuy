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


class UserBehaviorContext(BaseModel):
    """
    User behavior context for personalized recommendations (Sparky-like).
    Collected from the Android app's local Room DB (UserInteraction table)
    and sent with every chat request to enable context-aware AI suggestions.
    """
    recent_categories: List[str] = Field(
        default_factory=list,
        description="Product categories the user has been exploring (e.g. ['Televisions', 'Laptops'])"
    )
    recent_skus: List[str] = Field(
        default_factory=list,
        description="SKUs of products the user has recently viewed or scanned"
    )
    favorite_manufacturers: List[str] = Field(
        default_factory=list,
        description="Brands the user prefers based on browsing history (e.g. ['Samsung', 'Apple'])"
    )
    interaction_count: int = Field(
        0,
        description="Total number of user interactions tracked"
    )


class ChatRequest(BaseModel):
    """Chat request from user"""
    message: str = Field(..., description="User's message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    user_context: Optional[UserBehaviorContext] = Field(
        None,
        description="User behavior context for personalized recommendations"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "I want to buy an iPhone 15 Pro",
                "session_id": "abc123",
                "user_context": {
                    "recent_categories": ["Televisions", "Home Theater"],
                    "recent_skus": ["6537851", "7625672"],
                    "favorite_manufacturers": ["Samsung", "Sony"],
                    "interaction_count": 12
                }
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
    suggested_questions: Optional[List[str]] = Field(
        None,
        description="AI-generated follow-up questions shown as tappable chips (max 3)"
    )
    
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
