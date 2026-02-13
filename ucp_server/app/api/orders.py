"""
Orders API endpoints
Manages order queries and status updates
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.dependencies import get_current_user_id
from app.services.order_service import OrderService
from app.schemas.order import OrderResponse, OrderItemResponse
from app.models.order import OrderStatus
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=List[OrderResponse])
async def get_user_orders(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get all orders for the current user
    
    Response:
    [
        {
            "id": 1,
            "order_number": "ORD-20260212-001",
            "total_amount": 999.99,
            "status": "confirmed",
            "items": [...],
            "created_at": "2026-02-12T10:00:00Z"
        }
    ]
    """
    try:
        logger.info(f"Getting orders for user {user_id}")
        orders = await OrderService.get_user_orders(db, user_id)
        
        # Convert to response format
        orders_response = []
        for order in orders:
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
            
            orders_response.append(
                OrderResponse(
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
            )
        
        return orders_response
    except Exception as e:
        logger.error(f"Error getting user orders: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get orders: {str(e)}")


@router.get("/{order_number}", response_model=OrderResponse)
async def get_order_by_number(
    order_number: str,
    db: Session = Depends(get_db)
):
    """
    Get order details by order number
    
    Example: GET /orders/ORD-20260212-001
    
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
        logger.info(f"Getting order {order_number}")
        order = await OrderService.get_order_by_number(db, order_number)
        
        if not order:
            raise HTTPException(status_code=404, detail=f"Order {order_number} not found")
        
        # Convert items to response
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting order: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get order: {str(e)}")


@router.put("/{order_number}/status")
async def update_order_status(
    order_number: str,
    status: OrderStatus,
    db: Session = Depends(get_db)
):
    """
    Update order status (Admin function)
    
    Request body:
    {
        "status": "shipped"
    }
    
    Available statuses: pending, confirmed, processing, shipped, delivered, cancelled
    """
    try:
        logger.info(f"Updating order {order_number} status to {status}")
        order = await OrderService.update_order_status(db, order_number, status)
        
        return {
            "message": f"Order {order_number} status updated to {status}",
            "order_number": order.order_number,
            "status": order.status
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating order status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update order status: {str(e)}")
