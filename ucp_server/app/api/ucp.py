"""
UCP Profile endpoint
Implements /.well-known/ucp for service discovery
"""
from fastapi import APIRouter
from app.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/.well-known/ucp")
async def get_ucp_profile():
    """
    UCP Profile Discovery Endpoint
    Returns service capabilities and endpoints
    """
    logger.info("UCP profile requested")
    
    profile = {
        "version": "1.0",
        "name": "Best Buy UCP Server",
        "description": "UCP Server integrating Best Buy API for AI shopping",
        "services": {
            "checkout": {
                "supported": True,
                "endpoints": {
                    "session_create": f"{settings.ucp_base_url}/checkout/session",
                    "session_update": f"{settings.ucp_base_url}/checkout/session/{{id}}/update",
                    "session_complete": f"{settings.ucp_base_url}/checkout/session/{{id}}/complete"
                }
            },
            "identity": {
                "supported": True,
                "guest_checkout": True,
                "oauth_endpoint": None  # Not implemented in MVP
            },
            "cart": {
                "supported": True,
                "endpoints": {
                    "add": f"{settings.ucp_base_url}/cart/add",
                    "view": f"{settings.ucp_base_url}/cart",
                    "update": f"{settings.ucp_base_url}/cart/items/{{sku}}",
                    "remove": f"{settings.ucp_base_url}/cart/items/{{sku}}",
                    "clear": f"{settings.ucp_base_url}/cart"
                }
            },
            "products": {
                "supported": True,
                "endpoints": {
                    "search": f"{settings.ucp_base_url}/products/search",
                    "get_by_sku": f"{settings.ucp_base_url}/products/{{sku}}",
                    "get_by_upc": f"{settings.ucp_base_url}/products/upc/{{upc}}",
                    "recommendations": f"{settings.ucp_base_url}/products/{{sku}}/recommendations"
                }
            },
            "orders": {
                "supported": True,
                "endpoints": {
                    "list": f"{settings.ucp_base_url}/orders",
                    "get": f"{settings.ucp_base_url}/orders/{{order_number}}"
                }
            }
        },
        "payment_handlers": ["mock_payment"],  # Simulated payment for MVP
        "public_key": _load_public_key_safe()
    }
    
    return profile


def _load_public_key_safe() -> str:
    """
    Load UCP public key for signature verification
    Returns empty string if key file doesn't exist (for development)
    """
    try:
        with open(settings.ucp_public_key_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"Public key file not found: {settings.ucp_public_key_path}")
        return ""
    except Exception as e:
        logger.error(f"Error loading public key: {e}")
        return ""
