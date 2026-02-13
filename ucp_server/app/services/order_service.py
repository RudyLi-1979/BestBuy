"""
Order Service
Business logic for order management
"""
from sqlalchemy.orm import Session
from app.models.order import Order, OrderItem, OrderStatus, CheckoutSession
from app.models.cart import CartItem
from app.schemas.order import OrderResponse, OrderItemResponse
from typing import List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class OrderService:
    """
    Order management business logic
    """
    
    @staticmethod
    def _generate_order_number() -> str:
        """
        Generate unique order number
        Format: ORD-YYYYMMDD-XXX
        """
        today = datetime.utcnow().strftime("%Y%m%d")
        import random
        sequence = random.randint(1, 999)
        return f"ORD-{today}-{sequence:03d}"
    
    @staticmethod
    async def create_order_from_session(
        db: Session, 
        session: CheckoutSession
    ) -> Order:
        """
        Create order from checkout session
        UCP Endpoint: POST /checkout/session/{id}/complete
        
        Args:
            db: Database session
            session: CheckoutSession instance
            
        Returns:
            Created Order
        """
        try:
            # Validate session has shipping info
            if not session.shipping_name or not session.shipping_address:
                raise ValueError("Shipping information is required")
            
            # Get cart items
            cart_items = db.query(CartItem).filter(CartItem.user_id == session.user_id).all()
            
            if not cart_items:
                raise ValueError("Cart is empty")
            
            # Create order
            order = Order(
                order_number=OrderService._generate_order_number(),
                user_id=session.user_id,
                shipping_name=session.shipping_name,
                shipping_address=session.shipping_address,
                shipping_city=session.shipping_city,
                shipping_postal_code=session.shipping_postal_code,
                shipping_country=session.shipping_country,
                total_amount=session.total_amount,
                status=OrderStatus.CONFIRMED
            )
            
            db.add(order)
            db.flush()  # Get order ID
            
            # Create order items from cart
            for cart_item in cart_items:
                order_item = OrderItem(
                    order_id=order.id,
                    sku=cart_item.sku,
                    name=cart_item.name,
                    price=cart_item.price,
                    quantity=cart_item.quantity,
                    image_url=cart_item.image_url
                )
                db.add(order_item)
            
            # Clear cart
            db.query(CartItem).filter(CartItem.user_id == session.user_id).delete()
            
            # Delete checkout session
            db.delete(session)
            
            db.commit()
            db.refresh(order)
            
            logger.info(f"Created order {order.order_number} for user {session.user_id}")
            return order
            
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating order from session: {e}")
            raise
    
    @staticmethod
    async def get_order_by_number(db: Session, order_number: str) -> Optional[Order]:
        """
        Get order by order number
        
        Args:
            db: Database session
            order_number: Order number
            
        Returns:
            Order or None
        """
        try:
            order = db.query(Order).filter(Order.order_number == order_number).first()
            return order
        except Exception as e:
            logger.error(f"Error getting order {order_number}: {e}")
            raise
    
    @staticmethod
    async def get_user_orders(db: Session, user_id: str) -> List[Order]:
        """
        Get all orders for a user
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            List of orders
        """
        try:
            orders = db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()
            logger.info(f"Retrieved {len(orders)} orders for user {user_id}")
            return orders
        except Exception as e:
            logger.error(f"Error getting orders for user {user_id}: {e}")
            raise
    
    @staticmethod
    async def update_order_status(
        db: Session, 
        order_number: str, 
        status: OrderStatus
    ) -> Order:
        """
        Update order status
        
        Args:
            db: Database session
            order_number: Order number
            status: New status
            
        Returns:
            Updated Order
        """
        try:
            order = await OrderService.get_order_by_number(db, order_number)
            
            if not order:
                raise ValueError(f"Order {order_number} not found")
            
            order.status = status
            db.commit()
            db.refresh(order)
            
            logger.info(f"Updated order {order_number} status to {status}")
            return order
            
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating order {order_number} status: {e}")
            raise
