"""
Best Buy API Client
Migrated from Android App's BestBuyApiService.kt and RetrofitClient.kt
"""
import httpx
import re
from typing import Optional, List, Dict, Any
from app.config import settings
from app.schemas.product import Product, ProductSearchResponse
from app.schemas.store import Store, StoreAvailability, StoreSearchResponse
from app.schemas.category import Category, CategorySearchResponse
from app.services.rate_limiter import RateLimiter
import logging
import urllib.parse

logger = logging.getLogger(__name__)

# Common category cache (reduces API calls for frequently used categories)
COMMON_CATEGORIES = {
    "laptops": "abcat0502000",
    "laptop": "abcat0502000",
    "all_laptops": "pcmcat138500050001",
    "desktops": "abcat0501000",
    "desktop": "abcat0501000",
    "all_desktops": "pcmcat143400050013",
    "cell_phones": "abcat0800000",
    "phones": "abcat0800000",
    "phone": "abcat0800000",
    "smartphones": "abcat0800000",
    "macbooks": "abcat0502000",  # Use Laptops category, filter by manufacturer=Apple
    "mac_mini": "abcat0501000",  # Mac mini is a desktop computer
    "imac": "abcat0501000",  # iMac is also a desktop computer
    "mac_pro": "abcat0501000",  # Mac Pro is a desktop workstation
    "mac_studio": "abcat0501000",  # Mac Studio is a desktop computer
}

# ── Sparky-like complementary category map ────────────────────────────────────
# Maps a product's Browse category ID to complementary search queries.
# Used by get_complementary_products() when alsoBought returns no results.
# search_products() is reliable and does NOT hit mostViewed quota limits.
CATEGORY_COMPLEMENT_MAP: Dict[str, List[str]] = {
    # TVs → Sound Bars / Speakers, Streaming Devices, TV Accessories (mounts, cables)
    "abcat0101000": ["abcat0204000", "pcmcat241600050001", "abcat0107000"],
    # Home Theater Projectors → Screens, Audio, Streaming
    "abcat0102000": ["abcat0204000", "pcmcat241600050001"],
    # Laptops → Laptop Accessories (bags/sleeves), External Monitors, Storage
    "abcat0502000": ["pcmcat209000050006", "abcat0513000", "abcat0504000"],
    # Desktops → Monitors, Keyboards & Mice, Storage
    "abcat0501000": ["abcat0513000", "pcmcat128500050004", "abcat0504000"],
    # Tablets → Tablet Cases & Accessories, Keyboards, Styluses
    "abcat0503000": ["pcmcat312100050015", "pcmcat209000050006", "abcat0504000"],
    # Cell Phones → Phone Cases & Accessories, Headphones, Chargers/Power Banks
    "abcat0800000": ["pcmcat312100050015", "abcat0204000", "pcmcat209000050006"],
    # Headphones / Earbuds → Carrying Cases, DACs & Amps, Cables
    "abcat0204000": ["pcmcat209000050006", "pcmcat241600050001"],
    # Cameras (Digital Cameras) → Lenses, Memory Cards, Camera Bags
    "abcat0400000": ["pcmcat232400050000", "abcat0504000", "pcmcat241600050001"],
    # DSLR Cameras → Lenses, Memory Cards, Flashes
    "abcat0401000": ["pcmcat232400050000", "abcat0504000"],
    # Gaming Consoles → Games, Controllers, Gaming Headsets
    "abcat0700000": ["abcat0702000", "abcat0707000", "abcat0204000"],
    # Printers → Ink & Toner, Paper, Printer Accessories
    "abcat0301000": ["pcmcat128500050004", "pcmcat241600050001"],
}

# ── Category name → fallback search queries (quota-safe) ─────────────────────
# Keys are lowercase category/product type names as seen in Room DB category strings.
# Used when alsoBought returns 0 results — ONE targeted search_products call.
CATEGORY_NAME_TO_QUERIES: Dict[str, str] = {
    # TVs / Displays
    "televisions":            "soundbar speaker",
    "tv":                     "soundbar speaker",
    "television":             "soundbar speaker",
    "oled":                   "soundbar speaker",
    "qled":                   "soundbar speaker",
    "4k tv":                  "soundbar speaker",
    "monitors":               "monitor stand webcam",
    "monitor":                "monitor stand webcam",
    "projectors":             "soundbar projector screen",
    # Computers
    "laptops":                "laptop bag USB hub",
    "laptop":                 "laptop bag USB hub",
    "notebooks":              "laptop bag external monitor",
    "macbooks":               "laptop bag USB hub",
    "desktops":               "monitor keyboard mouse",
    "desktop":                "monitor keyboard mouse",
    "tablets":                "tablet case keyboard",
    "tablet":                 "tablet case keyboard",
    "ipads":                  "iPad case keyboard",
    # Mobile
    "cell phones":            "phone case wireless earbuds",
    "cell phone":             "phone case wireless earbuds",
    "smartphones":            "phone case wireless earbuds",
    "iphones":                "iPhone case wireless earbuds",
    # Audio
    "headphones":             "headphone stand audio cable",
    "headphone":              "headphone stand audio cable",
    "earbuds":                "earbuds case wireless charger",
    "speakers":               "speaker stand audio cable",
    # Cameras
    "cameras":                "camera memory card camera bag",
    "camera":                 "camera memory card camera bag",
    "digital cameras":        "camera memory card camera bag",
    "dslr":                   "camera lens memory card",
    # Gaming
    "video games":            "gaming headset game controller",
    "gaming":                 "gaming headset game controller",
    "game consoles":          "gaming headset controller",
    "playstation":            "PlayStation controller gaming headset",
    "xbox":                   "Xbox controller gaming headset",
    "nintendo":               "Nintendo Switch case controller",
    # Smart Home
    "smart home":             "smart plug smart bulb hub",
    "networking":             "WiFi extender Ethernet switch",
    # Printers
    "printers":               "printer ink cartridge paper",
    "printer":                "printer ink cartridge paper",
}

def _get_complement_query(category_hints: list, manufacturer_hint: str = None) -> str:
    """
    Derive a single targeted search query from category/manufacturer hints — NO API call needed.
    Returns the first match found in CATEGORY_NAME_TO_QUERIES.
    Manufacturer hint is NOT appended to avoid pulling unrelated brand products.
    """
    for cat in category_hints:
        key = cat.lower().strip()
        if key in CATEGORY_NAME_TO_QUERIES:
            return CATEGORY_NAME_TO_QUERIES[key]
    # Keyword scan as last resort
    cat_str = " ".join(category_hints).lower()
    for keyword, query in [
        ("tv", "soundbar speaker"), ("television", "soundbar speaker"),
        ("laptop", "laptop bag USB hub"), ("phone", "phone case wireless earbuds"),
        ("camera", "camera memory card camera bag"), ("game", "gaming headset controller"),
        ("tablet", "tablet case keyboard"),
    ]:
        if keyword in cat_str:
            return query
    return ""  # give up — no fallback query available


class BestBuyAPIClient:
    """
    Best Buy API Client
    Provides methods to interact with Best Buy Developer API
    """
    
    def __init__(self):
        self.base_url = settings.bestbuy_api_base_url
        self.api_key = settings.bestbuy_api_key
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Initialize rate limiter (5 req/min, 50,000 req/day — free developer tier)
        self.rate_limiter = RateLimiter(
            requests_per_minute=5,
            requests_per_day=50000
        )
        
        # Category cache to reduce API calls
        self._category_cache: Dict[str, Category] = {}  # category_id -> Category
        self._search_cache: Dict[str, CategorySearchResponse] = {}  # search_name -> response
        self._category_cache_initialized = False
        
        logger.info(f"Initialized Best Buy API Client with base URL: {self.base_url}")
        logger.info("Rate limiting enabled: 5 req/min, 50,000 req/day")
        logger.info(f"Common category cache loaded: {len(COMMON_CATEGORIES)} categories")
    
    async def search_by_upc(self, upc: str) -> Optional[Product]:
        """
        Search product by UPC barcode
        Mirrors BestBuyApiService.searchProductByUPC()
        
        Args:
            upc: Product UPC barcode
            
        Returns:
            Product if found, None otherwise
        """
        try:
            # Rate limiting
            await self.rate_limiter.acquire()
            
            url = f"{self.base_url}/v1/products(upc={upc})"
            params = {
                "apiKey": self.api_key,
                "format": "json",
                "show": "sku,name,regularPrice,salePrice,onSale,image,largeFrontImage,mediumImage,thumbnailImage,longDescription,shortDescription,manufacturer,modelNumber,upc,url,addToCartUrl,customerReviewAverage,customerReviewCount,freeShipping,inStoreAvailability,onlineAvailability"
            }
            
            logger.info(f"Searching product by UPC: {upc}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("total", 0) > 0:
                product = Product(**data["products"][0])
                logger.info(f"Found product: {product.name} (SKU: {product.sku})")
                return product
            
            logger.warning(f"No product found for UPC: {upc}")
            return None
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error searching by UPC {upc}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error searching by UPC {upc}: {e}")
            raise
    
    async def get_product_by_sku(self, sku: str) -> Optional[Product]:
        """
        Get product by SKU
        Mirrors BestBuyApiService.getProductBySKU()
        
        Args:
            sku: Product SKU
            
        Returns:
            Product if found, None otherwise
        """
        try:
            # Rate limiting
            await self.rate_limiter.acquire()
            
            url = f"{self.base_url}/v1/products/{sku}.json"
            params = {
                "apiKey": self.api_key,
                "show": "sku,name,regularPrice,salePrice,onSale,image,largeFrontImage,mediumImage,thumbnailImage,longDescription,shortDescription,manufacturer,modelNumber,upc,url,addToCartUrl,customerReviewAverage,customerReviewCount,freeShipping,inStoreAvailability,onlineAvailability,categoryPath"
            }
            
            logger.info(f"Getting product by SKU: {sku}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            product = Product(**response.json())
            logger.info(f"Found product: {product.name}")
            return product
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Product not found for SKU: {sku}")
                return None
            logger.error(f"HTTP error getting product by SKU {sku}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting product by SKU {sku}: {e}")
            raise
    
    async def search_products(
        self, 
        query: str, 
        page_size: int = 10,
        sort: Optional[str] = None
    ) -> ProductSearchResponse:
        """
        Search products by keyword with intelligent filtering
        Mirrors BestBuyApiService.searchProducts()
        
        Args:
            query: Search keyword with specifications
            page_size: Number of results (max 100)
            sort: Sort order (e.g., "name.asc", "salePrice.desc")
            
        Returns:
            ProductSearchResponse with filtered and ranked products
        """
        try:
            # Rate limiting
            await self.rate_limiter.acquire()
            
            # Best Buy API uses "products(search=query)" format
            # We need to URL encode the query (e.g., "mac mini" -> "mac%20mini")
            encoded_query = urllib.parse.quote(query)
            url = f"{self.base_url}/v1/products(search={encoded_query})"
            
            # Request more results for better filtering (but limit to conserve API quota)
            # For device searches, we need more results because gift cards/warranties appear first
            request_size = min(page_size * 4, 50)  # Request 4x to filter down, max 50
            
            params = {
                "apiKey": self.api_key,
                "format": "json",
                "show": "sku,name,regularPrice,salePrice,onSale,image,mediumImage,thumbnailImage,shortDescription,manufacturer,modelNumber,upc,url",
                "pageSize": request_size,
            }
            
            # Use best-selling rank for device searches to prioritize actual products over gift cards/warranties
            # For other searches, use name sorting for consistency
            device_keywords = ['iphone', 'ipad', 'macbook', 'laptop', 'phone', 'tablet', 'watch', 'airpods', 'mac mini', 'imac']
            is_device_search = any(keyword in query.lower() for keyword in device_keywords)
            
            if sort:
                params["sort"] = sort
            elif is_device_search:
                params["sort"] = "bestSellingRank.asc"  # Best sellers first - real products, not gift cards
                logger.info(f"Device search detected, using bestSellingRank.asc sorting")
            else:
                params["sort"] = "name.asc"  # Name sorting for non-device searches
            
            logger.info(f"Searching products with query: {query}")
            logger.debug(f"Request URL: {url}")
            logger.debug(f"Request Params: {params}")
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            # Parse response and handle missing pagination fields
            data = response.json()
            total = data.get("total", 0)
            products = [Product(**p) for p in data.get("products", [])]
            
            # Best Buy API may not return pagination fields with products(search=...) format
            # Provide sensible defaults
            result = ProductSearchResponse(
                total=total,
                products=products,
                from_=data.get("from", 1),
                to=data.get("to", min(request_size, len(products))),
                current_page=data.get("currentPage", 1),
                total_pages=data.get("totalPages", (total + request_size - 1) // request_size if request_size > 0 else 1)
            )
            
            logger.info(f"Found {result.total} products for query: {query}")
            
            # Apply intelligent filtering and ranking
            result = self._filter_and_rank_results(query, result, page_size)
            
            logger.info(f"After filtering: {len(result.products)} products")
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error searching products with query '{query}': {e}")
            raise
        except Exception as e:
            logger.error(f"Error searching products with query '{query}': {e}")
            raise
    
    def _filter_and_rank_results(self, query: str, result: ProductSearchResponse, max_results: int) -> ProductSearchResponse:
        """
        Filter and rank search results based on query relevance
        
        Args:
            query: Original search query
            result: Initial search results
            max_results: Maximum number of results to return
            
        Returns:
            Filtered and ranked ProductSearchResponse
        """
        if not result.products:
            return result
        
        query_lower = query.lower()
        query_terms = set(query_lower.split())
        
        # Extract product type from query for type matching
        product_type_keywords = {
            'iphone': ['iphone'],
            'ipad': ['ipad'],
            'macbook': ['macbook'],
            'imac': ['imac'],
            'mac mini': ['mac mini'],
            'mac pro': ['mac pro'],
            'mac studio': ['mac studio'],
            'airpods': ['airpods', 'air pods'],
            'watch': ['watch', 'apple watch'],
            'laptop': ['laptop', 'notebook'],
            'phone': ['phone', 'smartphone'],
            'tablet': ['tablet'],
            'headphones': ['headphones', 'earbuds', 'earphones'],
            'tv': ['tv', 'television'],
            'monitor': ['monitor', 'display']
        }
        
        # Detect product type from query
        detected_product_type = None
        for product_type, keywords in product_type_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                detected_product_type = product_type
                logger.info(f"Detected product type from query: {product_type}")
                break
        
        # Extract potential specs from query (storage sizes, colors, etc.)
        specs = []
        for term in query_terms:
            # Storage sizes: 64GB, 128GB, 256GB, 512GB, 1TB, 2TB, etc.
            if 'gb' in term.lower() or 'tb' in term.lower():
                specs.append(term)
            # Colors: black, white, silver, gold, etc.
            elif term.lower() in ['black', 'white', 'silver', 'gold', 'blue', 'red', 'green', 'purple', 'pink', 'yellow']:
                specs.append(term)
        
        logger.info(f"Extracted specs from query '{query}': {specs}")
        
        # Define irrelevant product types to filter out
        # Use word boundaries to avoid false positives (e.g., "gift" matching "gifted")
        irrelevant_keywords = [
            'gift card', 'giftcard', 'e-gift', 'egift', 'gift cards',
            'warranty', 'protection plan', 'geek squad',
            'membership', 'subscription', 
            'installation service', 'setup service', 'tech support',
            'applecare', 'apple care'
        ]
        
        def is_irrelevant_product(product_text: str, product_name: str = "") -> tuple[bool, str]:
            """
            Check if product is an irrelevant type (gift card, warranty, service)
            Uses more precise matching to avoid false positives
            Returns: (is_irrelevant, matched_keyword)
            """
            product_lower = product_text.lower()
            
            # Check for exact phrase matches
            for keyword in irrelevant_keywords:
                # Use word boundaries for single words, exact match for phrases
                if ' ' in keyword:  # Multi-word phrase
                    if keyword in product_lower:
                        logger.info(f"  🔍 Matched keyword '{keyword}' (phrase) in: {product_name[:70]}")
                        return True, keyword
                else:  # Single word - check with word boundaries
                    # Check if keyword appears as a standalone word
                    if re.search(r'\b' + re.escape(keyword) + r'\b', product_lower):
                        logger.info(f"  🔍 Matched keyword '{keyword}' (word boundary) in: {product_name[:70]}")
                        return True, keyword
            
            return False, ""
        
        # Score each product
        scored_products = []
        irrelevant_filtered = []  # Track filtered irrelevant products
        
        logger.info(f"Starting product filtering for {len(result.products)} products...")
        
        for product in result.products:
            score = 0
            product_text = f"{product.name} {product.short_description or ''} {product.model_number or ''}".lower()
            
            # FILTER: Skip irrelevant product types (gift cards, warranties, services)
            is_irrelevant, matched_keyword = is_irrelevant_product(product_text, product.name)
            if is_irrelevant:
                logger.info(f"❌ FILTERED (matched '{matched_keyword}'): {product.name[:80]}")
                irrelevant_filtered.append(product.name)
                continue
            else:
                logger.info(f"✅ KEPT (relevant): {product.name[:80]}")
            
            # FILTER: If user is searching for a device (phone, laptop, etc.), skip accessories
            # unless the query explicitly mentions accessories
            device_keywords = ['iphone', 'ipad', 'macbook', 'laptop', 'phone', 'tablet', 'watch', 'airpods']
            # NOTE: 'case' intentionally excluded — Apple Watch/iPhone bodies also contain "Aluminum Case"/"Titanium Case"
            # Accessory detection is primarily handled by the is_accessory_by_pattern check below
            accessory_keywords = ['charger', 'cable', 'adapter', 'stand', 'mount', 'screen protector']
            
            is_device_search = any(device in query_lower for device in device_keywords)
            is_accessory_product = any(accessory in product_text for accessory in accessory_keywords)
            accessory_in_query = any(accessory in query_lower for accessory in accessory_keywords)

            # Additional check: "for <device>" pattern → accessory for the device
            # e.g., "Sport Band for Apple Watch 44mm" when user searches "Apple Watch"
            # Apple Watch DEVICES say "with Sport Band", not "for Apple Watch"
            is_accessory_by_pattern = False
            if detected_product_type and is_device_search and not accessory_in_query:
                type_kws = product_type_keywords.get(detected_product_type, [])
                for type_kw in type_kws:
                    if f"for {type_kw}" in product_text:
                        is_accessory_by_pattern = True
                        logger.info(f"  🔍 Accessory pattern 'for {type_kw}' matched: {product.name[:70]}")
                        break

            if is_device_search and (is_accessory_product or is_accessory_by_pattern) and not accessory_in_query:
                logger.debug(f"Product '{product.name}' is an accessory, but user searched for device, skipping")
                continue
            
            # FILTER: Product type mismatch (e.g., searching "iPhone" but got "iPad")
            if detected_product_type:
                product_name_lower = product.name.lower()
                
                # Define conflicting product types (mutually exclusive)
                conflicts = {
                    'iphone': ['ipad', 'ipod', 'macbook', 'imac', 'mac mini', 'mac pro', 'apple watch'],
                    'ipad': ['iphone', 'macbook', 'imac', 'mac mini', 'mac pro'],
                    'macbook': ['iphone', 'ipad', 'imac', 'mac mini', 'mac pro', 'mac studio'],
                    'mac mini': ['iphone', 'ipad', 'macbook', 'imac', 'mac pro', 'mac studio', 'laptop'],
                    'imac': ['iphone', 'ipad', 'macbook', 'mac mini', 'mac pro', 'mac studio', 'laptop'],
                    'mac pro': ['iphone', 'ipad', 'macbook', 'mac mini', 'imac', 'mac studio', 'laptop'],
                    'mac studio': ['iphone', 'ipad', 'macbook', 'mac mini', 'imac', 'mac pro', 'laptop'],
                    'laptop': ['phone', 'tablet', 'watch'],
                    'phone': ['tablet', 'laptop', 'watch', 'ipad'],
                    'tablet': ['phone', 'laptop', 'watch', 'iphone']
                }
                
                # Check if product name contains conflicting type
                has_conflict = False
                if detected_product_type in conflicts:
                    for conflicting_type in conflicts[detected_product_type]:
                        if conflicting_type in product_name_lower:
                            logger.debug(f"Product '{product.name}' is {conflicting_type}, but user searched for {detected_product_type}, skipping")
                            has_conflict = True
                            break
                
                if has_conflict:
                    continue  # Skip this product entirely
                
                # Check if product matches expected type (bonus points)
                type_keywords = product_type_keywords.get(detected_product_type, [])
                if any(keyword in product_name_lower for keyword in type_keywords):
                    score += 200  # Strong bonus for correct product type match
                    logger.debug(f"Product '{product.name}' matches expected type {detected_product_type}, +200 score")
            
            # Exact query match in name (highest priority)
            if query_lower in product.name.lower():
                score += 100
            
            # Check if all specs are present in product text
            specs_matched = 0
            specs_missing = []
            for spec in specs:
                if spec in product_text:
                    specs_matched += 1
                    score += 50  # Bonus for matching spec
                else:
                    specs_missing.append(spec)
            
            # Penalize products missing specs, but don't skip them entirely
            # This allows fallback results when no products match all specs
            if specs and specs_matched < len(specs):
                score -= (len(specs_missing) * 30)  # Penalty for each missing spec
                logger.debug(f"Product '{product.name}' missing specs {specs_missing}, score penalty applied (matched {specs_matched}/{len(specs)})")
            
            # Skip products with very low scores (negative or near-zero)
            if score < 0:
                logger.debug(f"Product '{product.name}' score too low ({score}), skipping")
                continue
            
            # All query terms present (important)
            terms_found = sum(1 for term in query_terms if term in product_text)
            score += terms_found * 10
            
            # Prefer products with model numbers when query has them
            if product.model_number and any(term.replace(' ', '').isalnum() and len(term) > 3 for term in query_terms):
                score += 20
            
            # Availability bonus
            if product.online_availability:
                score += 5
            
            scored_products.append((score, product))
            logger.debug(f"Product '{product.name}' scored: {score}")
        
        # Sort by score (descending) and take top results
        scored_products.sort(key=lambda x: x[0], reverse=True)
        filtered_products = [p for score, p in scored_products[:max_results]]
        
        logger.info(f"Filtered from {len(result.products)} to {len(filtered_products)} products (irrelevant: {len(irrelevant_filtered)}, filtered by score/specs: {len(result.products) - len(irrelevant_filtered) - len(filtered_products)})")
        
        # Log sample of filtered products for debugging
        if not filtered_products and irrelevant_filtered:
            logger.info(f"Sample of irrelevant products filtered: {irrelevant_filtered[:3]}")
        
        # FALLBACK: If filtering removed all products, check if we should return some results
        if not filtered_products and result.products:
            # If MOST products (80%+) are irrelevant types, return empty (truly bad query)
            irrelevant_count = len(irrelevant_filtered)
            irrelevant_ratio = irrelevant_count / len(result.products)

            if irrelevant_ratio >= 0.8:
                logger.warning(f"Most products ({irrelevant_count}/{len(result.products)}, {irrelevant_ratio:.0%}) are irrelevant types. Returning empty results.")
                filtered_products = []
            else:
                # Scoring filtered everything — return top scored products as fallback
                non_irrelevant_count = len(result.products) - irrelevant_count
                if scored_products:
                    logger.warning(f"Score filter removed all {non_irrelevant_count} relevant products. Returning top {max_results} as fallback.")
                    # Re-sort (already sorted) and return top results ignoring score threshold
                    scored_products.sort(key=lambda x: x[0], reverse=True)
                    filtered_products = [p for _, p in scored_products[:max_results]]
                else:
                    logger.info(f"{non_irrelevant_count} products were relevant but all filtered pre-scoring. Returning empty.")
                    filtered_products = []
        
        # Calculate pagination info
        total_filtered = len(filtered_products)
        to_index = min(max_results, total_filtered)
        
        return ProductSearchResponse(
            total=total_filtered,
            products=filtered_products[:max_results],
            from_=1,
            to=to_index,
            current_page=1,
            total_pages=1
        )
    
    async def get_recommendations(self, sku: str) -> List[Product]:
        """
        Get product recommendations (Also Viewed)
        Mirrors BestBuyApiService.getRecommendations()
        
        Args:
            sku: Product SKU
            
        Returns:
            List of recommended products
        """
        try:
            # Rate limiting
            await self.rate_limiter.acquire()
            
            url = f"{self.base_url}/v1/products/{sku}/alsoViewed"
            params = {"apiKey": self.api_key}
            
            logger.info(f"Getting recommendations for SKU: {sku}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            products = [Product(**p) for p in data.get("products", [])]
            logger.info(f"Found {len(products)} recommendations for SKU: {sku}")
            return products
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting recommendations for SKU {sku}: {e}")
            return []  # Return empty list on error
        except Exception as e:
            logger.error(f"Error getting recommendations for SKU {sku}: {e}")
            return []
    
    async def get_similar_products(self, sku: str) -> List[Product]:
        """
        Get similar products
        Mirrors BestBuyApiService.getSimilarProducts()
        
        Args:
            sku: Product SKU
            
        Returns:
            List of similar products
        """
        try:
            # Rate limiting
            await self.rate_limiter.acquire()
            
            url = f"{self.base_url}/beta/products/{sku}/similar"
            params = {"apiKey": self.api_key}
            
            logger.info(f"Getting similar products for SKU: {sku}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            products = [Product(**p) for p in data.get("products", [])]
            logger.info(f"Found {len(products)} similar products for SKU: {sku}")
            return products
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting similar products for SKU {sku}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting similar products for SKU {sku}: {e}")
            return []
    
    async def get_store_availability(
        self,
        sku: str,
        postal_code: Optional[str] = None,
        radius: int = 25,
        max_stores: int = 3
    ) -> StoreSearchResponse:
        """
        Check product availability at nearby stores (BOPIS - Buy Online, Pick-up In Store)
        
        Args:
            sku: Product SKU
            postal_code: ZIP/Postal code for location (e.g., "94103")
            radius: Search radius in miles (default: 25)
            max_stores: Maximum number of stores to return (default: 3, reduced for API quota)
            
        Returns:
            StoreSearchResponse with availability information
        """
        product_name = None  # Initialize to avoid UnboundLocalError
        
        try:
            # Rate limiting
            await self.rate_limiter.acquire()
            
            # Get product details first for product name
            product = await self.get_product_by_sku(sku)
            product_name = product.name if product else None
            
            # Build store availability query
            url = f"{self.base_url}/v1/stores"
            params = {
                "apiKey": self.api_key,
                "format": "json",
                "pageSize": max_stores
            }
            
            # Add location filter if postal code provided
            if postal_code:
                params["area"] = f"{postal_code},{radius}"
                logger.info(f"Checking store availability for SKU {sku} near {postal_code} (radius: {radius} miles)")
            else:
                logger.info(f"Checking store availability for SKU {sku} (no location filter)")
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            stores_data = response.json()
            
            stores = []
            if stores_data.get("total", 0) > 0:
                # For each store, check product availability
                for store_info in stores_data.get("stores", []):
                    try:
                        store = Store(**store_info)
                        
                        # Check product availability at this store
                        availability_url = f"{self.base_url}/v1/products/{sku}/stores/{store.store_id}"
                        availability_params = {"apiKey": self.api_key}
                        
                        await self.rate_limiter.acquire()
                        avail_response = await self.client.get(availability_url, params=availability_params)
                        avail_response.raise_for_status()
                        avail_data = avail_response.json()
                        
                        # Parse availability info
                        in_stock = avail_data.get("inStoreAvailability", False)
                        pickup_eligible = avail_data.get("pickupEligible", False)
                        ship_from_store = avail_data.get("shipFromStoreEligible", False)
                        
                        stores.append(StoreAvailability(
                            store=store,
                            sku=int(sku),
                            inStock=in_stock,
                            pickupEligible=pickup_eligible,
                            shipFromStoreEligible=ship_from_store
                        ))
                        
                        logger.debug(f"Store {store.name}: in_stock={in_stock}, pickup={pickup_eligible}")
                        
                    except Exception as e:
                        logger.warning(f"Error checking availability for store {store_info.get('storeId')}: {e}")
                        continue
            
            logger.info(f"Found availability at {len(stores)} stores for SKU {sku}")
            
            return StoreSearchResponse(
                sku=int(sku),
                productName=product_name,
                stores=stores,
                totalStores=len(stores)
            )
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error checking store availability for SKU {sku}: {e}")
            # product_name may be None if get_product_by_sku failed
            return StoreSearchResponse(sku=int(sku), productName=product_name or f"Product {sku}", stores=[], totalStores=0)
        except Exception as e:
            logger.error(f"Error checking store availability for SKU {sku}: {e}")
            return StoreSearchResponse(sku=int(sku), productName=product_name or f"Product {sku}", stores=[], totalStores=0)
    
    async def get_also_bought(self, sku: str) -> List[Product]:
        """
        Get products that customers also bought (cross-sell recommendations)
        
        Args:
            sku: Product SKU
            
        Returns:
            List of products frequently bought together
        """
        try:
            # Rate limiting
            await self.rate_limiter.acquire()
            
            url = f"{self.base_url}/v1/products/{sku}/alsoBought"
            params = {"apiKey": self.api_key}
            
            logger.info(f"Getting alsoBought recommendations for SKU: {sku}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            products = [Product(**p) for p in data.get("products", [])]
            logger.info(f"Found {len(products)} alsoBought products for SKU: {sku}")
            return products
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting alsoBought for SKU {sku}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting alsoBought for SKU {sku}: {e}")
            return []
    
    async def advanced_search(
        self,
        query: str,
        manufacturer: Optional[str] = None,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        on_sale: Optional[bool] = None,
        free_shipping: Optional[bool] = None,
        in_store_pickup: Optional[bool] = None,
        page_size: int = 10,
        sort: Optional[str] = None
    ) -> ProductSearchResponse:
        """
        Advanced product search with multiple filters and operators
        
        Args:
            query: Search query text
            manufacturer: Filter by manufacturer (e.g., "Apple", "Samsung")
            category: Filter by category name (e.g., "Cell Phones", "Laptops", "Tablets")
            min_price: Minimum price filter
            max_price: Maximum price filter
            on_sale: Filter for products on sale
            free_shipping: Filter for free shipping products
            in_store_pickup: Filter for in-store pickup availability
            page_size: Number of results to return
            sort: Sort order (e.g., "name.asc", "salePrice.asc", "regularPrice.desc")
            
        Returns:
            ProductSearchResponse with filtered results
        """
        try:
            # Rate limiting
            await self.rate_limiter.acquire()
            
            # NOTE: We do NOT auto-detect categories to avoid incorrect filtering
            # Best Buy's category structure must be queried from Categories API
            # We rely on:
            # 1. Manufacturer filtering (API-level) - highly effective
            # 2. Product type filtering (client-side) - filters gift cards, warranties, wrong device types
            # 3. Spec matching (client-side) - validates storage, colors, etc.
            
            # Build filter query using Best Buy API format
            # Best Buy uses products(filter1=value1&filter2=value2) format
            filters = []
            
            # Manufacturer filter (highest priority for brand-specific searches)
            if manufacturer:
                filters.append(f"manufacturer={urllib.parse.quote(manufacturer)}")
            
            # Category filter (only if explicitly provided by user)
            # Note: Common categories are cached in COMMON_CATEGORIES dict
            # To get valid categories, query Best Buy Categories API:
            # GET https://api.bestbuy.com/v1/categories?apiKey=KEY
            # Use categoryPath.id (e.g., abcat0400000) or categoryPath.name
            # 
            # Common category IDs:
            # - abcat0502000: Laptops
            # - abcat0501000: Desktops
            # - abcat0800000: Cell Phones
            if category:
                # Prefer categoryPath.id if available, otherwise use categoryPath.name
                if category.startswith('abcat'):
                    filters.append(f'categoryPath.id={category}')
                    logger.info(f"Using category ID filter: {category}")
                else:
                    filters.append(f'categoryPath.name="{urllib.parse.quote(category)}"')
                    logger.info(f"Using category name filter: {category}")
            
            # Base search query (after manufacturer filter)
            if query:
                filters.append(f"search={urllib.parse.quote(query)}")
            
            # Price range filter (using salePrice attribute)
            if min_price is not None and max_price is not None:
                filters.append(f"salePrice>={min_price}")
                filters.append(f"salePrice<={max_price}")
            elif min_price is not None:
                filters.append(f"salePrice>={min_price}")
            elif max_price is not None:
                filters.append(f"salePrice<={max_price}")
            
            # Boolean filters
            if on_sale is True:
                filters.append("onSale=true")
            
            if free_shipping is True:
                filters.append("freeShipping=true")
            
            if in_store_pickup is True:
                filters.append("inStoreAvailability=true")
            
            # Construct URL with Best Buy API format: products(filter1=value1&filter2=value2)
            filter_str = "&".join(filters)
            url = f"{self.base_url}/v1/products({filter_str})" if filters else f"{self.base_url}/v1/products"
            
            params = {
                "apiKey": self.api_key,
                "format": "json",
                "pageSize": min(page_size * 10, 100)  # Request 10x to get past gift cards/warranties (max 100)
            }
            # Add sort parameter if specified
            if sort:
                params["sort"] = sort
            else:
                # Use bestSellingRank to prioritize popular devices over gift cards
                params["sort"] = "bestSellingRank.asc"
            
            # Add show parameter to request specific fields
            params["show"] = "sku,name,regularPrice,salePrice,onSale,image,largeFrontImage,mediumImage,thumbnailImage,longDescription,shortDescription,manufacturer,modelNumber,upc,url,addToCartUrl,customerReviewAverage,customerReviewCount,freeShipping,inStoreAvailability,onlineAvailability"
            
            logger.info(f"Advanced search with filters: {filter_str if filters else 'none'}")
            logger.debug(f"Request URL: {url}")
            logger.debug(f"Request params: {params}")
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            total = data.get("total", 0)
            products = [Product(**p) for p in data.get("products", [])]
            
            logger.info(f"Advanced search found {total} products, returning {len(products)}")
            
            # Apply intelligent filtering if query provided
            if query and products:
                result = ProductSearchResponse(
                    total=total,
                    products=products,
                    from_=data.get("from", 1),
                    to=data.get("to", len(products)),
                    current_page=data.get("currentPage", 1),
                    total_pages=data.get("totalPages", 1)
                )
                return self._filter_and_rank_results(query, result, page_size)
            
            # Return without filtering
            return ProductSearchResponse(
                total=len(products[:page_size]),
                products=products[:page_size],
                from_=1,
                to=min(page_size, len(products)),
                current_page=1,
                total_pages=1
            )
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error in advanced search: {e}")
            return ProductSearchResponse(total=0, products=[], from_=1, to=0, current_page=1, total_pages=0)
        except Exception as e:
            logger.error(f"Error in advanced search: {e}")
            return ProductSearchResponse(total=0, products=[], from_=1, to=0, current_page=1, total_pages=0)
    
    async def get_categories(
        self,
        category_id: Optional[str] = None,
        page_size: int = 100
    ) -> CategorySearchResponse:
        """
        Get Best Buy categories from Categories API
        Can retrieve all categories or search for specific ones
        
        Args:
            category_id: Optional category ID to filter (e.g., 'abcat0400000')
            page_size: Number of results per page (default 100, max 100)
            
        Returns:
            CategorySearchResponse with list of categories
            
        Example:
            # Get all categories
            result = await client.get_categories()
            
            # Get specific category
            result = await client.get_categories(category_id="abcat0400000")
        """
        try:
            # Check cache first
            if category_id and category_id in self._category_cache:
                logger.info(f"Returning cached category: {category_id}")
                cached_cat = self._category_cache[category_id]
                return CategorySearchResponse(
                    total=1,
                    categories=[cached_cat],
                    from_=1,
                    to=1,
                    current_page=1,
                    total_pages=1
                )
            
            # Rate limiting
            await self.rate_limiter.acquire()
            
            # Build URL
            if category_id:
                url = f"{self.base_url}/v1/categories(id={category_id})"
            else:
                url = f"{self.base_url}/v1/categories"
            
            params = {
                "apiKey": self.api_key,
                "format": "json",
                "pageSize": min(page_size, 100),
                "show": "id,name,url,path,subCategories"
            }
            
            logger.info(f"Getting categories: {url}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            total = data.get("total", 0)
            categories = [Category(**cat) for cat in data.get("categories", [])]
            
            # Cache retrieved categories
            for cat in categories:
                self._category_cache[cat.id] = cat
            
            logger.info(f"Found {total} categories, returning {len(categories)}")
            
            return CategorySearchResponse(
                total=total,
                categories=categories,
                from_=data.get("from", 1),
                to=data.get("to", len(categories)),
                current_page=data.get("currentPage", 1),
                total_pages=data.get("totalPages", 1)
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting categories: {e}")
            return CategorySearchResponse(total=0, categories=[], from_=1, to=0, current_page=1, total_pages=0)
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return CategorySearchResponse(total=0, categories=[], from_=1, to=0, current_page=1, total_pages=0)
    
    async def search_categories(
        self,
        name: str,
        page_size: int = 20
    ) -> CategorySearchResponse:
        """
        Search for categories by name using wildcards
        
        Args:
            name: Category name to search (supports wildcards with *)
            page_size: Number of results per page (default 20, max 100)
            
        Returns:
            CategorySearchResponse with matching categories
            
        Example:
            # Search for camera categories
            result = await client.search_categories(name="Camera*")
            
            # Search for phone categories
            result = await client.search_categories(name="Phone*")
        """
        try:
            # Normalize name for cache lookup (remove wildcard, lowercase)
            cache_key = name.lower().rstrip('*').strip()
            
            # Check if this is a common category (use COMMON_CATEGORIES)
            if cache_key in COMMON_CATEGORIES:
                category_id = COMMON_CATEGORIES[cache_key]
                logger.info(f"Using cached common category ID for '{name}': {category_id}")
                return await self.get_categories(category_id=category_id)
            
            # Check search cache (for non-common categories)
            if cache_key in self._search_cache:
                logger.info(f"Returning cached search results for '{name}'")
                return self._search_cache[cache_key]
            
            # Rate limiting
            await self.rate_limiter.acquire()
            
            # Build search query
            # Use wildcard if not provided
            search_name = name if '*' in name else f"{name}*"
            # Don't URL-encode wildcards (*) - Best Buy API requires them literally
            url = f"{self.base_url}/v1/categories(name={urllib.parse.quote(search_name, safe='*')})"
            
            params = {
                "apiKey": self.api_key,
                "format": "json",
                "pageSize": min(page_size, 100),
                "show": "id,name,url,path,subCategories"
            }
            
            logger.info(f"Searching categories with name: {search_name}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            total = data.get("total", 0)
            categories = [Category(**cat) for cat in data.get("categories", [])]
            
            # Create response
            response_obj = CategorySearchResponse(
                total=total,
                from_=data.get("from", 1),
                to=data.get("to", len(categories)),
                current_page=data.get("currentPage", 1),
                total_pages=data.get("totalPages", 1),
                categories=categories
            )
            
            # Cache individual categories
            for cat in categories:
                self._category_cache[cat.id] = cat
            
            # Cache search result (using normalized name)
            self._search_cache[cache_key] = response_obj
            
            logger.info(f"Found {total} categories matching '{name}', returning {len(categories)} (cached for future searches)")
            
            # Log first few results for debugging
            if categories:
                for i, cat in enumerate(categories[:3]):
                    logger.debug(f"{i+1}. {cat.name} (ID: {cat.id})")
            
            return response_obj
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error searching categories: {e}")
            return CategorySearchResponse(total=0, categories=[], from_=1, to=0, current_page=1, total_pages=0)
        except Exception as e:
            logger.error(f"Error searching categories: {e}")
            return CategorySearchResponse(total=0, categories=[], from_=1, to=0, current_page=1, total_pages=0)

    async def get_complementary_products(
        self,
        sku: str,
        category_hints: list = None,
        manufacturer_hint: str = None,
    ) -> List[Product]:
        """
        Sparky-like: Return products that complement the given SKU.

        API call budget: MAX 2 calls (critical for 5 req/min quota).
          Call 1 — alsoBought(sku): Best Buy's "bought together" signal.
                   If ≥ 3 results → return immediately (only 1 call used).
          Call 2 — search_products(targeted query): fired ONLY when alsoBought
                   returns < 3 results. Query derived from category_hints
                   (passed from user's Room DB history — NO extra get_product_by_sku call).

        Args:
            sku:               SKU of the anchor product.
            category_hints:    List of category names from user_context.recent_categories
                               (e.g. ["Televisions", "Home Theater"]).
            manufacturer_hint: Preferred brand from user_context.favorite_manufacturers[0].

        Returns:
            List of ≤ 6 complementary products; empty list on error or zero results.
        """
        try:
            seen_skus = {str(sku)}
            results: List[Product] = []

            # ── Call 1: alsoBought ──────────────────────────────────────────────
            also_bought = await self.get_also_bought(sku)
            for p in also_bought:
                p_sku = str(p.sku)
                if p_sku not in seen_skus:
                    seen_skus.add(p_sku)
                    results.append(p)
            logger.info(f"alsoBought({sku}) → {len(results)} product(s)")

            if len(results) >= 3:
                # Good enough — save Call 2 for other API needs
                return results[:6]

            # ── Call 2: targeted search (only when alsoBought gives < 3) ───────
            if category_hints:
                fallback_query = _get_complement_query(category_hints, manufacturer_hint)
            else:
                fallback_query = ""

            if fallback_query:
                logger.info(f"alsoBought insufficient ({len(results)}); searching '{fallback_query}'")
                try:
                    search_result = await self.search_products(fallback_query, page_size=6)
                    for p in search_result.products:
                        p_sku = str(p.sku)
                        if p_sku not in seen_skus:
                            seen_skus.add(p_sku)
                            results.append(p)
                    logger.info(f"search_products('{fallback_query}') → {len(search_result.products)} additional")
                except Exception as e:
                    logger.warning(f"search_products('{fallback_query}') failed: {e}")
            else:
                logger.info(f"No category_hints provided and alsoBought returned {len(results)} — returning as-is")

            logger.info(f"get_complementary_products({sku}): returning {len(results)} product(s) total")
            return results[:6]

        except Exception as e:
            logger.error(f"Error in get_complementary_products for SKU {sku}: {e}")
            return []

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
