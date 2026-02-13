"""
Checkout Service
Business logic for checkout session management
"""
from sqlalchemy.orm import Session
from app.models.order import CheckoutSession
from app.models.cart import CartItem
from app.schemas.checkout import CheckoutSessionUpdate, CheckoutSessionResponse
from typing import Optional
from datetime import datetime, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)


class CheckoutService:
    """
    Checkout session business logic
    Implements UCP checkout flow
    """
    
    @staticmethod
    async def create_session(db: Session, user_id: str) -> CheckoutSession:
        """
        Create checkout session from user's cart
        UCP Endpoint: POST /checkout/session
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            CheckoutSession instance
        """
        try:
            # Get cart items
            cart_items = db.query(CartItem).filter(CartItem.user_id == user_id).all()
            
            if not cart_items:
                raise ValueError("Cart is empty")
            
            # Calculate total
            total = sum(item.price * item.quantity for item in cart_items)
            
            # Create session
            session_id = str(uuid.uuid4())
            session = CheckoutSession(
                id=session_id,
                user_id=user_id,
                total_amount=total,
                expires_at=datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
            )
            
            db.add(session)
            db.commit()
            db.refresh(session)
            
            logger.info(f"Created checkout session {session_id} for user {user_id}, total ${total:.2f}")
            return session
            
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating checkout session for user {user_id}: {e}")
            raise
    
    @staticmethod
    async def get_session(db: Session, session_id: str) -> Optional[CheckoutSession]:
        """
        Get checkout session by ID
        
        Args:
            db: Database session
            session_id: Session ID
            
        Returns:
            CheckoutSession or None
        """
        try:
            session = db.query(CheckoutSession).filter(CheckoutSession.id == session_id).first()
            
            if session and session.expires_at and session.expires_at < datetime.utcnow():
                logger.warning(f"Checkout session {session_id} has expired")
                return None
            
            return session
            
        except Exception as e:
            logger.error(f"Error getting checkout session {session_id}: {e}")
            raise
    
    @staticmethod
    async def update_session(
        db: Session, 
        session_id: str, 
        update_data: CheckoutSessionUpdate
    ) -> CheckoutSession:
        """
        Update checkout session with shipping information
        UCP Endpoint: POST /checkout/session/{id}/update
        
        Args:
            db: Database session
            session_id: Session ID
            update_data: Shipping information
            
        Returns:
            Updated CheckoutSession
        """
        try:
            session = await CheckoutService.get_session(db, session_id)
            
            if not session:
                raise ValueError(f"Checkout session {session_id} not found or expired")
            
            # Update shipping information
            session.shipping_name = update_data.shipping_name
            session.shipping_address = update_data.shipping_address
            session.shipping_city = update_data.shipping_city
            session.shipping_postal_code = update_data.shipping_postal_code
            session.shipping_country = update_data.shipping_country
            
            db.commit()
            db.refresh(session)
            
            logger.info(f"Updated checkout session {session_id} with shipping info")
            return session
            
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating checkout session {session_id}: {e}")
            raise
    
    @staticmethod
    async def delete_session(db: Session, session_id: str) -> bool:
        """
        Delete checkout session
        
        Args:
            db: Database session
            session_id: Session ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            session = db.query(CheckoutSession).filter(CheckoutSession.id == session_id).first()
            
            if not session:
                return False
            
            db.delete(session)
            db.commit()
            logger.info(f"Deleted checkout session {session_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting checkout session {session_id}: {e}")
            raise
