"""
Cart Service
Business logic for shopping cart operations
Based on Android App's CartRepository.kt
"""
from sqlalchemy.orm import Session
from app.models.cart import CartItem
from app.schemas.cart import CartItemCreate, CartResponse, CartItemResponse
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class CartService:
    """
    Shopping cart business logic
    Mirrors Android App's CartRepository
    """
    
    @staticmethod
    async def add_item(db: Session, user_id: str, item: CartItemCreate) -> CartItem:
        """
        Add item to cart or update quantity if exists
        Mirrors CartRepository.addItem()
        
        Args:
            db: Database session
            user_id: User ID
            item: Cart item to add
            
        Returns:
            CartItem instance
        """
        try:
            # Check if item already exists in cart
            existing = db.query(CartItem).filter(
                CartItem.user_id == user_id,
                CartItem.sku == item.sku
            ).first()
            
            if existing:
                # Update quantity
                existing.quantity += item.quantity
                logger.info(f"Updated cart item {item.sku} quantity to {existing.quantity} for user {user_id}")
            else:
                # Create new cart item
                existing = CartItem(
                    user_id=user_id,
                    sku=item.sku,
                    name=item.name,
                    price=item.price,
                    image_url=item.image_url,
                    quantity=item.quantity
                )
                db.add(existing)
                logger.info(f"Added new cart item {item.sku} for user {user_id}")
            
            db.commit()
            db.refresh(existing)
            return existing
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error adding item to cart for user {user_id}: {e}")
            raise
    
    @staticmethod
    async def get_cart(db: Session, user_id: str) -> CartResponse:
        """
        Get user's cart with total price
        Mirrors CartRepository.allItems
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            CartResponse with items and total
        """
        try:
            items = db.query(CartItem).filter(CartItem.user_id == user_id).all()
            
            # Convert to response schema
            item_responses = [
                CartItemResponse(
                    id=item.id,
                    user_id=item.user_id,
                    sku=item.sku,
                    name=item.name,
                    price=item.price,
                    image_url=item.image_url,
                    quantity=item.quantity,
                    subtotal=item.subtotal,
                    added_at=item.added_at
                )
                for item in items
            ]
            
            total = sum(item.subtotal for item in items)
            
            logger.info(f"Retrieved cart for user {user_id}: {len(items)} items, total ${total:.2f}")
            
            return CartResponse(
                items=item_responses,
                total_price=total,
                item_count=len(items)
            )
            
        except Exception as e:
            logger.error(f"Error getting cart for user {user_id}: {e}")
            raise
    
    @staticmethod
    async def update_quantity(db: Session, user_id: str, sku: str, quantity: int) -> Optional[CartItem]:
        """
        Update item quantity or remove if quantity <= 0
        Mirrors CartRepository.updateQuantity()
        
        Args:
            db: Database session
            user_id: User ID
            sku: Product SKU
            quantity: New quantity (0 to remove)
            
        Returns:
            Updated CartItem or None if removed
        """
        try:
            item = db.query(CartItem).filter(
                CartItem.user_id == user_id,
                CartItem.sku == sku
            ).first()
            
            if not item:
                logger.warning(f"Cart item {sku} not found for user {user_id}")
                raise ValueError(f"Item {sku} not found in cart")
            
            if quantity <= 0:
                # Remove item
                db.delete(item)
                db.commit()
                logger.info(f"Removed cart item {sku} for user {user_id}")
                return None
            
            # Update quantity
            item.quantity = quantity
            db.commit()
            db.refresh(item)
            logger.info(f"Updated cart item {sku} quantity to {quantity} for user {user_id}")
            return item
            
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating cart item {sku} for user {user_id}: {e}")
            raise
    
    @staticmethod
    async def remove_item(db: Session, user_id: str, sku: str) -> bool:
        """
        Remove item from cart
        Mirrors CartRepository.removeItem()
        
        Args:
            db: Database session
            user_id: User ID
            sku: Product SKU
            
        Returns:
            True if removed, False if not found
        """
        try:
            item = db.query(CartItem).filter(
                CartItem.user_id == user_id,
                CartItem.sku == sku
            ).first()
            
            if not item:
                logger.warning(f"Cart item {sku} not found for user {user_id}")
                return False
            
            db.delete(item)
            db.commit()
            logger.info(f"Removed cart item {sku} for user {user_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error removing cart item {sku} for user {user_id}: {e}")
            raise
    
    @staticmethod
    async def clear_cart(db: Session, user_id: str) -> int:
        """
        Clear all items from cart
        Mirrors CartRepository.clearCart()
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Number of items removed
        """
        try:
            count = db.query(CartItem).filter(CartItem.user_id == user_id).delete()
            db.commit()
            logger.info(f"Cleared cart for user {user_id}: {count} items removed")
            return count
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error clearing cart for user {user_id}: {e}")
            raise
