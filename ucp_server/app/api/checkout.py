"""
Checkout API endpoints
Implements UCP checkout flow
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user_id
from app.services.checkout_service import CheckoutService
from app.services.order_service import OrderService
from app.schemas.checkout import CheckoutSessionCreate, CheckoutSessionUpdate, CheckoutSessionResponse
from app.schemas.order import OrderResponse, OrderItemResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/session", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Create checkout session from user's cart
    UCP Standard Endpoint
    
    Response:
    {
        "id": "uuid",
        "user_id": "guest_abc123",
        "total_amount": 999.99,
        "created_at": "2026-02-12T10:00:00Z"
    }
    """
    try:
        logger.info(f"Creating checkout session for user {user_id}")
        session = await CheckoutService.create_session(db, user_id)
        
        return CheckoutSessionResponse(
            id=session.id,
            user_id=session.user_id,
            total_amount=session.total_amount,
            shipping_name=session.shipping_name,
            shipping_address=session.shipping_address,
            shipping_city=session.shipping_city,
            shipping_postal_code=session.shipping_postal_code,
            shipping_country=session.shipping_country,
            created_at=session.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {str(e)}")


@router.post("/session/{session_id}/update", response_model=CheckoutSessionResponse)
async def update_checkout_session(
    session_id: str,
    update_data: CheckoutSessionUpdate,
    db: Session = Depends(get_db)
):
    """
    Update checkout session with shipping information
    UCP Standard Endpoint
    
    Request body:
    {
        "shipping_name": "John Doe",
        "shipping_address": "123 Main St",
        "shipping_city": "New York",
        "shipping_postal_code": "10001",
        "shipping_country": "US"
    }
    """
    try:
        logger.info(f"Updating checkout session {session_id}")
        session = await CheckoutService.update_session(db, session_id, update_data)
        
        return CheckoutSessionResponse(
            id=session.id,
            user_id=session.user_id,
            total_amount=session.total_amount,
            shipping_name=session.shipping_name,
            shipping_address=session.shipping_address,
            shipping_city=session.shipping_city,
            shipping_postal_code=session.shipping_postal_code,
            shipping_country=session.shipping_country,
            created_at=session.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating checkout session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update checkout session: {str(e)}")


@router.post("/session/{session_id}/complete", response_model=OrderResponse)
async def complete_checkout(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Complete checkout and create order
    UCP Standard Endpoint
    
    This will:
    1. Create an order from the checkout session
    2. Clear the user's cart
    3. Delete the checkout session
    
    Response:
    {
        "id": 1,
        "order_number": "ORD-20260212-001",
        "total_amount": 999.99,
        "status": "confirmed",
        "items": [...]
    }
    """
    try:
        logger.info(f"Completing checkout session {session_id}")
        
        # Get session
        session = await CheckoutService.get_session(db, session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Checkout session {session_id} not found or expired")
        
        # Create order
        order = await OrderService.create_order_from_session(db, session)
        
        # Convert to response
        items_response = [
            OrderItemResponse(
                id=item.id,
                sku=item.sku,
                name=item.name,
                price=item.price,
                quantity=item.quantity,
                subtotal=item.subtotal,
                image_url=item.image_url
            )
            for item in order.items
        ]
        
        return OrderResponse(
            id=order.id,
            order_number=order.order_number,
            user_id=order.user_id,
            shipping_name=order.shipping_name,
            shipping_address=order.shipping_address,
            shipping_city=order.shipping_city,
            shipping_postal_code=order.shipping_postal_code,
            shipping_country=order.shipping_country,
            total_amount=order.total_amount,
            status=order.status,
            items=items_response,
            created_at=order.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing checkout: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to complete checkout: {str(e)}")


@router.get("/session/{session_id}", response_model=CheckoutSessionResponse)
async def get_checkout_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get checkout session details
    
    Response:
    {
        "id": "uuid",
        "user_id": "guest_abc123",
        "total_amount": 999.99,
        "shipping_name": "John Doe",
        ...
    }
    """
    try:
        logger.info(f"Getting checkout session {session_id}")
        session = await CheckoutService.get_session(db, session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"Checkout session {session_id} not found or expired")
        
        return CheckoutSessionResponse(
            id=session.id,
            user_id=session.user_id,
            total_amount=session.total_amount,
            shipping_name=session.shipping_name,
            shipping_address=session.shipping_address,
            shipping_city=session.shipping_city,
            shipping_postal_code=session.shipping_postal_code,
            shipping_country=session.shipping_country,
            created_at=session.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting checkout session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get checkout session: {str(e)}")
