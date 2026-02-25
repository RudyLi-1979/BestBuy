"""
Product schemas for Best Buy API responses
Mirrors Android App's Product.kt data class
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class ProductSimple(BaseModel):
    """
    Simplified product model for chat responses and product cards
    Contains only essential information for display
    """
    sku: int
    name: str
    sale_price: Optional[float] = Field(None, alias="salePrice")
    regular_price: Optional[float] = Field(None, alias="regularPrice")
    on_sale: Optional[bool] = Field(None, alias="onSale")
    manufacturer: Optional[str] = None
    image: Optional[str] = None
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "sku": 6428324,
                "name": "Apple - iPhone 15 Pro 128GB - Natural Titanium",
                "salePrice": 899.99,
                "regularPrice": 999.99,
                "onSale": True,
                "manufacturer": "Apple",
                "image": "https://pisces.bbystatic.com/image2/BestBuy_US/images/products/6428/6428324_sd.jpg"
            }
        }


class CategoryPathItem(BaseModel):
    """Single level in the Best Buy product category hierarchy (e.g. Televisions)."""
    id: Optional[str] = None
    name: Optional[str] = None

    class Config:
        populate_by_name = True


class Product(BaseModel):
    """
    Product model matching Best Buy API response
    Based on Android App's Product data class

    """
    sku: Optional[int] = None
    name: Optional[str] = None
    regular_price: Optional[float] = Field(None, alias="regularPrice")
    sale_price: Optional[float] = Field(None, alias="salePrice")
    on_sale: Optional[bool] = Field(None, alias="onSale")
    image: Optional[str] = None
    large_front_image: Optional[str] = Field(None, alias="largeFrontImage")
    medium_image: Optional[str] = Field(None, alias="mediumImage")
    thumbnail_image: Optional[str] = Field(None, alias="thumbnailImage")
    long_description: Optional[str] = Field(None, alias="longDescription")
    short_description: Optional[str] = Field(None, alias="shortDescription")
    manufacturer: Optional[str] = None
    model_number: Optional[str] = Field(None, alias="modelNumber")
    upc: Optional[str] = None
    url: Optional[str] = None
    add_to_cart_url: Optional[str] = Field(None, alias="addToCartUrl")
    customer_review_average: Optional[float] = Field(None, alias="customerReviewAverage")
    customer_review_count: Optional[int] = Field(None, alias="customerReviewCount")
    free_shipping: Optional[bool] = Field(None, alias="freeShipping")
    in_store_availability: Optional[bool] = Field(None, alias="inStoreAvailability")
    online_availability: Optional[bool] = Field(None, alias="onlineAvailability")
    category_path: Optional[List[CategoryPathItem]] = Field(None, alias="categoryPath")
    
    class Config:
        populate_by_name = True  # Allow both alias and field name
        protected_namespaces = ()  # Disable protected namespace warning for model_number
        json_schema_extra = {
            "example": {
                "sku": 6428324,
                "name": "Apple - iPhone 15 Pro 128GB - Natural Titanium",
                "regularPrice": 999.99,
                "salePrice": 899.99,
                "onSale": True,
                "image": "https://pisces.bbystatic.com/image2/BestBuy_US/images/products/6428/6428324_sd.jpg",
                "manufacturer": "Apple",
                "upc": "195949038488"
            }
        }


class ProductSearchResponse(BaseModel):
    """
    Best Buy API search response wrapper
    """
    from_: int = Field(default=1, alias="from")
    to: int = Field(default=10)
    total: int
    current_page: int = Field(default=1, alias="currentPage")
    total_pages: int = Field(default=1, alias="totalPages")
    products: List[Product] = []
    
    class Config:
        populate_by_name = True
        protected_namespaces = ()  # Disable protected namespace warning
