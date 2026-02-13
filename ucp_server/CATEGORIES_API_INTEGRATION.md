# Categories API Integration

**Date**: 2026-02-13  
**Status**: ✅ Implemented and Tested

## Overview

Integrated Best Buy Categories API into UCP Server to enable Gemini AI to:
1. Query available product categories dynamically
2. Use correct category IDs in product searches
3. Avoid "0 results" from hardcoded/incorrect category names

## Problem Solved

**Before**: 
- Hardcoded category names (e.g., "Desktop Computers") didn't match Best Buy's actual structure
- Searches returned 0 results (e.g., Mac mini search failed)
- No way to discover valid categories

**After**:
- Dynamic category lookup via Best Buy Categories API
- Use actual category IDs (e.g., `abcat0502000`) from API
- Gemini can search categories before filtering products

## Implementation

### 1. New Schema: `category.py`

```python
class Category(BaseModel):
    id: str                              # e.g., "abcat0502000"
    name: str                            # e.g., "Laptops"
    url: Optional[str]                   # BestBuy.com category page
    path: Optional[List[CategoryPath]]   # Hierarchical path
    subCategories: Optional[List[SubCategory]]
```

### 2. New Methods in `bestbuy_client.py`

#### `get_categories(category_id=None, page_size=100)`
Get all categories or specific category by ID.

```python
# Get all categories
result = await client.get_categories()

# Get specific category
result = await client.get_categories(category_id="abcat0502000")
```

#### `search_categories(name, page_size=20)`
Search categories by name with wildcard support.

⚠️ **Important**: Best Buy API only supports **trailing wildcards** (`word*`), not leading (`*word`) or both sides (`*word*`).

```python
# ✅ Correct: Trailing wildcard
result = await client.search_categories(name="Laptop*")
result = await client.search_categories(name="Phone*")

# ❌ Wrong: Leading or both sides (returns 400 Bad Request)
result = await client.search_categories(name="*Phone*")
result = await client.search_categories(name="*Laptop")
```

### 3. New Function in `gemini_client.py`

Added `search_categories` function declaration for Gemini AI:

```python
{
    "name": "search_categories",
    "description": "Search Best Buy Categories API to find valid category IDs...",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Category name with wildcards (*)"
            }
        }
    }
}
```

### 4. Handler in `chat_service.py`

Processes Gemini's `search_categories` calls and returns formatted results:

```python
elif function_name == "search_categories":
    result = await self.bestbuy_client.search_categories(name=name)
    return {
        "success": True,
        "categories": [...],
        "message": "Use 'id' field in advanced_product_search"
    }
```

## Workflow

### Recommended Usage Pattern

```
User: "Show me Mac mini"
   ↓
Gemini: [Calls search_categories(name="Desktop*")]
   ↓
System: Returns categories with IDs
   ↓
Gemini: [Calls advanced_product_search(
    query="Mac mini",
    manufacturer="Apple",
    category="abcat0501000"  ← Uses actual category ID
)]
   ↓
Result: ✅ Mac mini products found!
```

### Without Categories API (Old Way)

```
User: "Show me Mac mini"
   ↓
System: Uses hardcoded category="Desktop Computers"
   ↓
Result: ❌ 0 products (category name doesn't exist)
```

## Testing

### Test 1: Basic Categories Search

```bash
python test_categories_simple.py
```

**Result**: 
- Found 82 laptop categories
- Successfully retrieved `abcat0502000` (Laptops)
- Path: Best Buy > Computers & Tablets > Laptops

### Test 2: Gemini Integration

```bash
python test_gemini_categories.py
```

Tests Gemini calling categories API and using results.

## API Endpoints Used

```
GET /v1/categories
GET /v1/categories(id={categoryId})
GET /v1/categories(name={searchTerm})
```

**Query Parameters**:
- `apiKey`: API key
- `format`: json
- `pageSize`: 1-100 (default 100)
- `show`: id,name,url,path,subCategories

## Key Category IDs Discovered

| Category | ID | Path | Total Found |
|----------|----|----|-------------|
| **Laptops** | `abcat0502000` | Computers & Tablets > Laptops | 82 categories |
| All Laptops | `pcmcat138500050001` | Computers & Tablets > Laptops > All Laptops | (subcategory) |
| MacBooks | (subcategory) | Under All Laptops | (subcategory) |
| Windows Laptops | (subcategory) | Under All Laptops | (subcategory) |
| **Desktop Computers** | `abcat0501000` | Computers & Tablets > Desktop & All-in-One Computers | 31 categories |
| All Desktops | `pcmcat143400050013` | Computers & Tablets > Desktop & All-in-One Computers > All Desktops | (subcategory) |
| **Cell Phones** | `abcat0800000` | Cell Phones | 96 categories |
| Prepaid Phones & Plans | `abcat0801002` | Cell Phones > Prepaid Phones & Plans | (subcategory) |
| Cell Phone Accessories | `abcat0811002` | Cell Phones > Cell Phone Accessories | (subcategory) |

### Most Useful Category IDs for Product Search

```python
# Primary categories (use these in advanced_product_search)
LAPTOPS = "abcat0502000"           # All laptop computers
DESKTOPS = "abcat0501000"          # Desktop & All-in-One computers  
CELL_PHONES = "abcat0800000"       # All cell phones

# More specific subcategories
ALL_LAPTOPS = "pcmcat138500050001" # Excludes accessories/memory
ALL_DESKTOPS = "pcmcat143400050013" # Excludes accessories
```

## Updated Gemini Instructions

Added to `SHOPPING_ASSISTANT_INSTRUCTION`:

```
STEP 2: CHOOSE SEARCH METHOD
...
- For CATEGORY-BASED searches → First use search_categories
  * Workflow: 
    1. search_categories(name="Laptop*") to get category IDs
    2. Use returned category ID in advanced_product_search
  * Why: Category IDs ensure accurate filtering
```

## Benefits

1. **Dynamic Discovery**: No hardcoded category names
2. **Zero False Negatives**: Won't block valid products with wrong categories
3. **Future-Proof**: Automatically adapts to Best Buy's category changes
4. **User Exploration**: Users can ask "What categories exist?"

## Limitations

1. **API Quota**: Each category search = 1 API call
2. **Wildcards Required**: Must use `*` for partial matches
3. **URL Encoding**: Wildcards must NOT be encoded (fixed with `safe='*'`)

## Error Handling

```python
# 400 Bad Request: Invalid category name format
# 403 Over Quota: Daily API limit exceeded
# Solution: Graceful fallback to manufacturer-only filtering
```

## Next Steps

1. ✅ Remove hardcoded `category_mapping` dict
2. ✅ Update Gemini to query categories when needed
3. ⏳ Cache frequently used categories (future optimization)
4. ⏳ Add categories to search suggestions (UI enhancement)

## Files Modified

- ✅ `app/schemas/category.py` (NEW)
- ✅ `app/services/bestbuy_client.py` (+150 lines)
- ✅ `app/services/gemini_client.py` (+30 lines)
- ✅ `app/services/chat_service.py` (+25 lines)
- ✅ `test_categories.py` (NEW)
- ✅ `test_gemini_categories.py` (NEW)
- ✅ `test_categories_simple.py` (NEW)

## API Call Impact

**Before**: 1-2 calls per product search  
**After**: 2-3 calls per search (if category lookup needed)  

**Optimization**: Cache category results for session.

---

**Status**: Ready for production use with API quota monitoring.
