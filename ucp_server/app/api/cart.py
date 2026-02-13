"""
Cart API endpoints
Manages shopping cart operations
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.dependencies import get_current_user_id
from app.services.cart_service import CartService
from app.schemas.cart import CartItemCreate, CartItemResponse, CartResponse, CartItemUpdate
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/add", response_model=CartItemResponse)
async def add_to_cart(
    item: CartItemCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Add item to cart or update quantity if exists
    
    Request body:
    {
        "sku": "6428324",
        "name": "iPhone 15 Pro",
        "price": 999.99,
        "image_url": "https://...",
        "quantity": 1
    }
    """
    try:
        logger.info(f"Adding item to cart for user {user_id}: {item.sku}")
        cart_item = await CartService.add_item(db, user_id, item)
        
        return CartItemResponse(
            id=cart_item.id,
            user_id=cart_item.user_id,
            sku=cart_item.sku,
            name=cart_item.name,
            price=cart_item.price,
            image_url=cart_item.image_url,
            quantity=cart_item.quantity,
            subtotal=cart_item.subtotal,
            added_at=cart_item.added_at
        )
    except Exception as e:
        logger.error(f"Error adding item to cart: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add item to cart: {str(e)}")


@router.get("", response_model=CartResponse)
async def get_cart(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get user's cart with all items and total price
    
    Response:
    {
        "items": [...],
        "total_price": 999.99,
        "item_count": 1
    }
    """
    try:
        logger.info(f"Getting cart for user {user_id}")
        cart = await CartService.get_cart(db, user_id)
        return cart
    except Exception as e:
        logger.error(f"Error getting cart: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cart: {str(e)}")


@router.put("/items/{sku}", response_model=Optional[CartItemResponse])
async def update_cart_item(
    sku: str,
    update: CartItemUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Update cart item quantity
    Set quantity to 0 to remove item
    
    Request body:
    {
        "quantity": 2
    }
    """
    try:
        logger.info(f"Updating cart item {sku} for user {user_id} to quantity {update.quantity}")
        cart_item = await CartService.update_quantity(db, user_id, sku, update.quantity)
        
        if not cart_item:
            return None  # Item was removed
        
        return CartItemResponse(
            id=cart_item.id,
            user_id=cart_item.user_id,
            sku=cart_item.sku,
            name=cart_item.name,
            price=cart_item.price,
            image_url=cart_item.image_url,
            quantity=cart_item.quantity,
            subtotal=cart_item.subtotal,
            added_at=cart_item.added_at
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating cart item: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update cart item: {str(e)}")


@router.delete("/items/{sku}")
async def remove_cart_item(
    sku: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Remove item from cart
    
    Response:
    {
        "message": "Item removed from cart"
    }
    """
    try:
        logger.info(f"Removing cart item {sku} for user {user_id}")
        removed = await CartService.remove_item(db, user_id, sku)
        
        if not removed:
            raise HTTPException(status_code=404, detail=f"Item {sku} not found in cart")
        
        return {"message": "Item removed from cart"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing cart item: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove cart item: {str(e)}")


@router.delete("")
async def clear_cart(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Clear all items from cart
    
    Response:
    {
        "message": "Cart cleared",
        "items_removed": 3
    }
    """
    try:
        logger.info(f"Clearing cart for user {user_id}")
        count = await CartService.clear_cart(db, user_id)
        return {
            "message": "Cart cleared",
            "items_removed": count
        }
    except Exception as e:
        logger.error(f"Error clearing cart: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cart: {str(e)}")
