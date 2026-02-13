"""
Store schemas for Best Buy API Store Availability responses
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class Store(BaseModel):
    """
    Store model matching Best Buy Store API response
    Used for "BOPIS" (Buy Online, Pick-up In Store) queries
    """
    store_id: Optional[int] = Field(None, alias="storeId")
    store_type: Optional[str] = Field(None, alias="storeType")
    name: Optional[str] = None
    address: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    postal_code: Optional[str] = Field(None, alias="postalCode")
    country: Optional[str] = None
    phone: Optional[str] = None
    distance: Optional[float] = None  # Distance from search location in miles
    detailed_hours: Optional[str] = Field(None, alias="detailedHours")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "storeId": 1118,
                "storeType": "BigBox",
                "name": "Best Buy - San Francisco",
                "address": "1717 Harrison St",
                "city": "San Francisco",
                "region": "CA",
                "postalCode": "94103",
                "distance": 0.5
            }
        }


class StoreAvailability(BaseModel):
    """
    Product availability at a specific store
    """
    store: Store
    sku: int
    in_stock: bool = Field(alias="inStock")
    pickup_available: bool = Field(alias="pickupEligible")
    ship_from_store_available: bool = Field(False, alias="shipFromStoreEligible")
    
    class Config:
        populate_by_name = True


class StoreSearchResponse(BaseModel):
    """
    Response for store availability searches
    """
    sku: int
    product_name: Optional[str] = Field(None, alias="productName")
    stores: List[StoreAvailability] = []
    total_stores: int = Field(0, alias="totalStores")
    
    class Config:
        populate_by_name = True
