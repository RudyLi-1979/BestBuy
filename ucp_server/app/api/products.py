"""
Products API endpoints
Integrates with Best Buy API for product search and details
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.bestbuy_client import BestBuyAPIClient
from app.schemas.product import Product, ProductSearchResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize Best Buy API Client
bestbuy_client = BestBuyAPIClient()


@router.get("/search", response_model=ProductSearchResponse)
async def search_products(
    q: str = Query(..., description="Search query keyword"),
    page_size: int = Query(10, ge=1, le=100, description="Number of results (1-100)"),
    sort: Optional[str] = Query(None, description="Sort order (e.g., 'name.asc', 'salePrice.desc')")
):
    """
    Search products by keyword
    
    Example: GET /products/search?q=iPhone&page_size=10&sort=salePrice.asc
    """
    try:
        logger.info(f"Searching products with query: {q}")
        result = await bestbuy_client.search_products(query=q, page_size=page_size, sort=sort)
        return result
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search products: {str(e)}")


@router.get("/{sku}", response_model=Product)
async def get_product_by_sku(sku: str):
    """
    Get product details by SKU
    
    Example: GET /products/6428324
    """
    try:
        logger.info(f"Getting product by SKU: {sku}")
        product = await bestbuy_client.get_product_by_sku(sku)
        
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with SKU {sku} not found")
        
        return product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product by SKU {sku}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get product: {str(e)}")


@router.get("/upc/{upc}", response_model=Product)
async def get_product_by_upc(upc: str):
    """
    Get product details by UPC barcode
    
    Example: GET /products/upc/195949038488
    """
    try:
        logger.info(f"Getting product by UPC: {upc}")
        product = await bestbuy_client.search_by_upc(upc)
        
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with UPC {upc} not found")
        
        return product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product by UPC {upc}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get product: {str(e)}")


@router.get("/{sku}/recommendations", response_model=list[Product])
async def get_product_recommendations(sku: str):
    """
    Get product recommendations (Also Viewed)
    
    Example: GET /products/6428324/recommendations
    """
    try:
        logger.info(f"Getting recommendations for SKU: {sku}")
        recommendations = await bestbuy_client.get_recommendations(sku)
        return recommendations
    except Exception as e:
        logger.error(f"Error getting recommendations for SKU {sku}: {e}")
        # Return empty list instead of error for better UX
        return []


@router.get("/{sku}/similar", response_model=list[Product])
async def get_similar_products(sku: str):
    """
    Get similar products
    
    Example: GET /products/6428324/similar
    """
    try:
        logger.info(f"Getting similar products for SKU: {sku}")
        similar = await bestbuy_client.get_similar_products(sku)
        return similar
    except Exception as e:
        logger.error(f"Error getting similar products for SKU {sku}: {e}")
        # Return empty list instead of error for better UX
        return []
