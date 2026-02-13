"""
Category schemas for Best Buy Categories API
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class CategoryPath(BaseModel):
    """Category path item representing hierarchy"""
    id: str = Field(..., description="Category ID (e.g., 'abcat0400000')")
    name: str = Field(..., description="Category name (e.g., 'Cameras & Camcorders')")


class SubCategory(BaseModel):
    """Subcategory information"""
    id: str = Field(..., description="Subcategory ID")
    name: str = Field(..., description="Subcategory name")


class Category(BaseModel):
    """Best Buy Category"""
    id: str = Field(..., description="Category ID (e.g., 'abcat0400000')")
    name: str = Field(..., description="Category name")
    url: Optional[str] = Field(None, description="URL to category page on BestBuy.com")
    path: Optional[List[CategoryPath]] = Field(None, description="Hierarchical path from root")
    subCategories: Optional[List[SubCategory]] = Field(None, alias="subCategories", description="Subcategories under this category")
    
    class Config:
        populate_by_name = True


class CategorySearchResponse(BaseModel):
    """Response from Categories API search"""
    total: int = Field(..., description="Total number of categories found")
    categories: List[Category] = Field(default_factory=list, description="List of categories")
    from_: int = Field(1, alias="from", description="Starting index")
    to: int = Field(0, description="Ending index")
    current_page: int = Field(1, alias="currentPage", description="Current page number")
    total_pages: int = Field(0, alias="totalPages", description="Total pages")
    
    class Config:
        populate_by_name = True
