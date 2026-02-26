"""
Gemini LLM Client
Integrates with Gemini 2.0 Flash for AI-powered shopping conversations
"""
import httpx
from typing import List, Dict, Any, Optional
from app.config import settings
import logging
import json

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Gemini API Client for conversational AI
    Supports Function Calling for UCP Server integration
    """
    
    def __init__(self):
        self.api_url = settings.gemini_api_url
        self.api_key = settings.gemini_api_key
        self.client = httpx.AsyncClient(timeout=60.0)
        logger.info(f"Initialized Gemini Client with URL: {self.api_url}")
    
    def get_function_declarations(self) -> List[Dict[str, Any]]:
        """
        Define available functions for Gemini Function Calling
        These functions map to UCP Server capabilities
        """
        return [
            {
                "name": "search_products",
                "description": """Basic product search by keyword. 

⚠️ LIMITATION: Cannot filter by brand/manufacturer - may return gift cards, accessories, or unrelated items.

WHEN TO USE:
- Generic searches without specific brand (rare cases)
- Searching by generic product type when user hasn't specified brand
  
WHEN NOT TO USE:
- ❌ Specific brand products (iPhone, MacBook, Samsung, etc.)
  → Use advanced_product_search with manufacturer filter instead!

If user searches for specific brand products, always prefer advanced_product_search.

By default, return only 2 results to conserve API quota.""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query text. Be specific and include all user-mentioned details."
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return. DEFAULT: 2 to conserve API quota. Only increase if user explicitly asks for more options (e.g., 'show me more', 'give me 5 options').",
                            "default": 2
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "search_by_upc",
                "description": "Search for a product by UPC (Universal Product Code) barcode. Use this when user mentions a UPC code or scanned a barcode.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "upc": {
                            "type": "string",
                            "description": "UPC barcode number (e.g., '400064431688')"
                        }
                    },
                    "required": ["upc"]
                }
            },
            {
                "name": "get_product_details",
                "description": "Get detailed information about a specific product by SKU",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sku": {
                            "type": "string",
                            "description": "Product SKU identifier"
                        }
                    },
                    "required": ["sku"]
                }
            },
            {
                "name": "add_to_cart",
                "description": "Add a product to the shopping cart. Use this when user wants to purchase or add items.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sku": {
                            "type": "string",
                            "description": "Product SKU"
                        },
                        "quantity": {
                            "type": "integer",
                            "description": "Quantity to add (default: 1)",
                            "default": 1
                        }
                    },
                    "required": ["sku"]
                }
            },
            {
                "name": "view_cart",
                "description": "View the current shopping cart contents and total price",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "remove_from_cart",
                "description": "Remove a product from the shopping cart",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sku": {
                            "type": "string",
                            "description": "Product SKU to remove"
                        }
                    },
                    "required": ["sku"]
                }
            },
            {
                "name": "update_cart_quantity",
                "description": "Update the quantity of a product in the cart",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sku": {
                            "type": "string",
                            "description": "Product SKU"
                        },
                        "quantity": {
                            "type": "integer",
                            "description": "New quantity"
                        }
                    },
                    "required": ["sku", "quantity"]
                }
            },
            {
                "name": "start_checkout",
                "description": "Start the checkout process. Use this when user wants to complete their purchase.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_product_recommendations",
                "description": "Get product recommendations based on a specific product",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sku": {
                            "type": "string",
                            "description": "Product SKU to get recommendations for"
                        }
                    },
                    "required": ["sku"]
                }
            },
            {
                "name": "check_store_availability",
                "description": "Check product availability at nearby physical stores for in-store pickup (BOPIS - Buy Online, Pick-up In Store). IMPORTANT: Only call this function when user EXPLICITLY asks about store availability, local stores, or in-store pickup. DO NOT call automatically during product search - wait for user to ask 'where can I buy this?', 'what stores have this?', 'can I pick up in store?', or when user mentions a zip code.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sku": {
                            "type": "string",
                            "description": "Product SKU to check availability for"
                        },
                        "product_name": {
                            "type": "string",
                            "description": "Full name of the product (e.g. 'Apple AirPods Pro 2nd Gen'). Pass this when you already know the product name to avoid an extra API lookup."
                        },
                        "postal_code": {
                            "type": "string",
                            "description": "ZIP/Postal code for location search (e.g., '94103', '10001'). If the user has not provided one, use the default test ZIP '55423' (Richfield, Minnesota) automatically — do NOT ask the user for their ZIP code."
                        },
                        "radius": {
                            "type": "integer",
                            "description": "Search radius in miles (default: 25)",
                            "default": 25
                        }
                    },
                    "required": ["sku"]
                }
            },
            {
                "name": "get_also_bought_products",
                "description": "Get products that customers frequently bought together with a specific product (cross-sell recommendations). Use this to suggest complementary purchases or bundle deals.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sku": {
                            "type": "string",
                            "description": "Product SKU to get also-bought recommendations for"
                        }
                    },
                    "required": ["sku"]
                }
            },
            {
                "name": "advanced_product_search",
                "description": """Advanced product search with multiple filters. **PREFERRED METHOD** for searching specific brand products like iPhones, MacBooks, Samsung phones, etc.

USE THIS FUNCTION when:
1. User mentions specific brand (Apple, Samsung, Sony, Dell, HP, LG, etc.)
2. User wants price filtering ("under $1000", "between $500-$800")
3. User wants sale items or shipping filters

CRITICAL: Use 'manufacturer' filter to avoid gift cards/accessories!

Examples:
✅ "iPhone 15 Pro 256GB" → advanced_product_search(query="iPhone 15 Pro 256GB", manufacturer="Apple")
✅ "MacBook Pro 16 inch" → advanced_product_search(query="MacBook Pro 16", manufacturer="Apple")  
✅ "Mac mini" → advanced_product_search(query="mac mini", manufacturer="Apple", category="abcat0501000")
✅ "iMac 27 inch" → advanced_product_search(query="iMac 27", manufacturer="Apple", category="abcat0501000")
✅ "Samsung phone under $800" → advanced_product_search(query="Galaxy", manufacturer="Samsung", max_price=800)
✅ "Sony headphones on sale" → advanced_product_search(query="headphones", manufacturer="Sony", on_sale=True)
✅ "Dell laptops" → advanced_product_search(query="laptop", manufacturer="Dell")
✅ "PlayStation 5" → advanced_product_search(query="PlayStation 5 console", manufacturer="Sony", category="abcat0700000")
✅ "PS5" → advanced_product_search(query="PlayStation 5 console", manufacturer="Sony", category="abcat0700000")
✅ "Xbox Series X" → advanced_product_search(query="Xbox Series X console", manufacturer="Microsoft", category="abcat0700000")
✅ "Nintendo Switch 2" → advanced_product_search(query="Nintendo Switch 2", manufacturer="Nintendo", category="abcat0700000")
✅ "Nintendo Switch" → advanced_product_search(query="Nintendo Switch console", manufacturer="Nintendo", category="abcat0700000")

Common manufacturers: Apple, Samsung, Sony, LG, Dell, HP, Lenovo, Microsoft, Google, Bose, Canon, Nikon, Nintendo""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query text (product model, type, keywords)"
                        },
                        "manufacturer": {
                            "type": "string",
                            "description": "Filter by manufacturer brand name. HIGHLY RECOMMENDED for specific brand searches. Examples: 'Apple', 'Samsung', 'Sony', 'LG', 'Dell', 'HP', 'Microsoft', 'Google'"
                        },
                        "category": {
                            "type": "string",
                            "description": "Best Buy category ID to filter results. Use known IDs for specific product types; otherwise omit. Known IDs: Laptops='abcat0502000', Desktops='abcat0501000', Cell Phones='abcat0800000', Game Consoles='abcat0700000', Video Games='abcat0702000', Game Controllers='abcat0707000'. ⚠️ For unknown categories, use search_categories first."
                        },
                        "min_price": {
                            "type": "number",
                            "description": "Minimum price filter in USD (e.g., 500 for $500)"
                        },
                        "max_price": {
                            "type": "number",
                            "description": "Maximum price filter in USD (e.g., 2000 for $2000)"
                        },
                        "on_sale": {
                            "type": "boolean",
                            "description": "Filter for products currently on sale/discounted"
                        },
                        "free_shipping": {
                            "type": "boolean",
                            "description": "Filter for products with free shipping"
                        },
                        "in_store_pickup": {
                            "type": "boolean",
                            "description": "Filter for products available for in-store pickup"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "search_categories",
                "description": """Search Best Buy Categories API to find valid category IDs and names.

USE THIS when:
- User asks about available categories
- Need to find correct category for filtering product searches
- Want to see what product categories Best Buy offers

WORKFLOW:
1. Search categories first: search_categories(name="Laptop*")
2. Get category ID from results (e.g., "abcat0502000")
3. Then use in product search: advanced_product_search(query="...", category="abcat0502000")

COMMON CATEGORY IDs (use these directly, no need to search):
- Laptops: "abcat0502000" (82 subcategories including MacBooks, Windows Laptops)
- Desktops: "abcat0501000" (31 subcategories including Mac mini, iMac, Mac Pro, Mac Studio)
- Cell Phones: "abcat0800000" (96 subcategories)
- All Laptops: "pcmcat138500050001" (excludes accessories/memory)
- All Desktops: "pcmcat143400050013" (excludes accessories)

Mac Product Categories:
- MacBook (laptops): Use "abcat0502000" + manufacturer="Apple"
- Mac mini (desktop): Use "abcat0501000" + manufacturer="Apple"
- iMac (desktop): Use "abcat0501000" + manufacturer="Apple"
- Mac Pro (desktop): Use "abcat0501000" + manufacturer="Apple"
- Mac Studio (desktop): Use "abcat0501000" + manufacturer="Apple"

Gaming Categories:
- Game Consoles (hardware): "abcat0700000" — ALWAYS use this when searching PlayStation/Xbox/Nintendo console hardware
- Video Games: "abcat0702000" — use this when user wants game titles
- Game Controllers: "abcat0707000"

Examples:
✅ "What laptop categories exist?" → search_categories(name="Laptop*")
✅ "Find phone categories" → search_categories(name="Phone*")
✅ "What camera categories are there?" → search_categories(name="Camera*")
✅ "Show me MacBooks" → advanced_product_search(query="MacBook", manufacturer="Apple", category="abcat0502000")

Returns: List of categories with ID, name, and URL for each.""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Category name to search for. ⚠️ Use trailing wildcard only: 'Laptop*', 'Phone*', 'Camera*'. Best Buy API does NOT support leading wildcards."
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "get_complementary_products",
                "description": """Find complementary products for a given product (Sparky-like proactive recommendation).

Use this PROACTIVELY after presenting a product to the user — even without an explicit request:
- When user views / searches a TV → suggest sound bars, streaming sticks, wall mounts
- When user views / searches a Laptop → suggest laptop bags, monitors, keyboards/mice
- When user views / searches a Camera → suggest memory cards, lenses, camera bags
- When user views / searches a Phone → suggest phone cases, earbuds, power banks
- When user views / searches a Game Console → suggest games, controllers, gaming headsets

Always call this AFTER the primary product search to enrich the response with ecosystem recommendations.
Frame suggestions naturally, e.g.:
  "Since you're looking at TVs, you might also want to complete your home theater setup with..."
  "Customers who buy this laptop often also grab..."

Returns: List of complementary products across related categories.

CRITICAL: When this function returns success=True with a products list,
YOU MUST describe those products by name in your reply.
NEVER say "I don't have recommendations" when products are returned.""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sku": {
                            "type": "string",
                            "description": "SKU of the anchor product the user is viewing or just found"
                        }
                    },
                    "required": ["sku"]
                }
            },
            {
                "name": "get_open_box_options",
                "description": """Check if open box, refurbished, or Geek Squad Certified versions of a product are available at a lower price.

USE THIS FUNCTION when:
- User asks about open box, refurbished, used, or pre-owned options
- User asks "is there a cheaper version?" or "do you have a refurbished one?"
- User taps the chip "Are there open box or refurbished versions available?"
- User explicitly asks about certified refurbished items

RESPONSE FORMAT:
- If has_open_box=True: List the available conditions ("excellent" or "certified"), show the open_box_price vs new_price savings.
  * "excellent" = looks brand new, no flaws, includes all original accessories
  * "certified" = passed Geek Squad Certification process
- If has_open_box=False: Let user know there are currently no open box options.

DO NOT call this automatically during a product search — wait for explicit user interest.""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sku": {
                            "type": "string",
                            "description": "Product SKU to check for open box / refurbished availability"
                        }
                    },
                    "required": ["sku"]
                }
            }
        ]
    
    def build_system_instruction(self, user_context=None) -> str:
        """
        Build the dynamic system instruction for Gemini, optionally injecting
        user behavior context (recent_categories, recent_skus, favorite_manufacturers).
        
        Args:
            user_context: Optional UserBehaviorContext pydantic model from ChatRequest.
            
        Returns:
            Complete system instruction string with personalization context appended.
        """
        if user_context is None:
            return SHOPPING_ASSISTANT_INSTRUCTION

        ctx_lines = ["", ""]
        ctx_lines.append("═" * 70)
        ctx_lines.append("PERSONALIZED CONTEXT (from user's browsing/scan history on their device):")
        ctx_lines.append("═" * 70)

        if user_context.recent_categories:
            cats = ", ".join(user_context.recent_categories)
            ctx_lines.append(f"• Recently explored categories: {cats}")

        if user_context.favorite_manufacturers:
            brands = ", ".join(user_context.favorite_manufacturers)
            ctx_lines.append(f"• Preferred brands: {brands}")

        if user_context.recent_skus:
            skus = ", ".join(user_context.recent_skus[:5])
            ctx_lines.append(f"• Recently viewed product SKUs: {skus}")
            ctx_lines.append(f"  ↑ MOST RECENT SKU = {user_context.recent_skus[0]}")

        ctx_lines.append(f"• Total interactions tracked: {user_context.interaction_count}")
        ctx_lines.append("")
        ctx_lines.append("Use this context to:")
        ctx_lines.append("  1. Greet or acknowledge the user's taste naturally (do NOT recite raw data)")
        ctx_lines.append("  2. Prioritize results matching their preferred brands")
        ctx_lines.append("  3. Call get_complementary_products() ONLY when search returns a single product")
        ctx_lines.append("     OR user asks about one specific item — NOT for multi-product brand searches")
        ctx_lines.append('     e.g. "Since you\'ve been looking at TVs, here are some audio upgrades..."')
        ctx_lines.append("")
        ctx_lines.append("CRITICAL RULE — When user asks about accessories / what goes with it /")
        ctx_lines.append("  recommendations / complete the setup / what else should I get:")
        ctx_lines.append("  → IMMEDIATELY call get_complementary_products(sku=MOST_RECENT_SKU)")
        ctx_lines.append("  → Use the SKU from 'Recently viewed product SKUs' above")
        ctx_lines.append("  → Do NOT give generic text suggestions without calling the function first")
        ctx_lines.append("  → The function returns REAL Best Buy products — present them with names & prices")
        ctx_lines.append("═" * 70)

        return SHOPPING_ASSISTANT_INSTRUCTION + "\n".join(ctx_lines)

    async def chat(
        self,
        message: str = None,
        conversation_history: List[Dict[str, str]] = None,
        system_instruction: str = None,
        function_responses: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a chat message to Gemini with function calling support
        
        Args:
            message: User's message (optional if function_responses provided)
            conversation_history: Previous conversation messages
            system_instruction: System instruction for the AI
            function_responses: Function call results to send back to Gemini
            
        Returns:
            Gemini API response with text or function calls
        """
        try:
            # Build Gemini API URL with API key
            api_url = f"{self.api_url}/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
            
            # Prepare request payload in Gemini format
            contents = []
            
            # Add conversation history
            if conversation_history:
                for msg in conversation_history:
                    role = "user" if msg["role"] == "user" else "model"
                    contents.append({
                        "role": role,
                        "parts": [{"text": msg["content"]}]
                    })
            
            # Add function responses if provided
            if function_responses:
                # Per Gemini API docs, function responses should be sent with role "user"
                # https://ai.google.dev/gemini-api/docs/function-calling
                parts = []
                for func_resp in function_responses:
                    parts.append({
                        "functionResponse": {
                            "name": func_resp["name"],
                            "response": func_resp["response"]
                        }
                    })
                contents.append({
                    "role": "user",  # Must be "user", not "function"
                    "parts": parts
                })
            
            # Add current message if provided
            if message:
                contents.append({
                    "role": "user",
                    "parts": [{"text": message}]
                })
            
            payload = {
                "contents": contents,
                # Disable Gemini 2.5 Flash thinking mode.
                # thinkingBudget=0 turns off chain-of-thought, which fixes
                # empty responses and speeds up function-calling rounds.
                "generationConfig": {
                    "thinkingConfig": {
                        "thinkingBudget": 0
                    }
                }
            }
            
            # Add system instruction if provided
            if system_instruction:
                payload["system_instruction"] = {
                    "parts": [{"text": system_instruction}]
                }
            
            # Add function declarations for function calling
            payload["tools"] = [{
                "function_declarations": self.get_function_declarations()
            }]
            
            # Call Gemini API
            headers = {
                "Content-Type": "application/json"
            }
            
            if message:
                logger.info(f"Sending message to Gemini: {message[:100]}...")
            elif function_responses:
                logger.info(f"Sending {len(function_responses)} function response(s) to Gemini")
            else:
                logger.info("Sending request to Gemini")
            
            logger.debug(f"Gemini API payload: {json.dumps(payload, indent=2)}")
                
            response = await self.client.post(
                api_url,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Gemini response received")
            logger.debug(f"Gemini response: {json.dumps(result, indent=2)}")
            
            # Parse response
            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                content = candidate.get("content", {})
                parts = content.get("parts", [])
                
                # Extract text response
                text_response = ""
                function_calls = []
                
                for part in parts:
                    if "text" in part:
                        text_response += part["text"]
                    elif "functionCall" in part:
                        func_call = part["functionCall"]
                        function_calls.append({
                            "name": func_call["name"],
                            "arguments": func_call.get("args", {})
                        })
                
                return {
                    "message": text_response,
                    "function_calls": function_calls
                }
            else:
                logger.warning(f"Unexpected Gemini response format: {result}")
                return {
                    "message": "I received an unexpected response format.",
                    "function_calls": []
                }
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling Gemini API: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            raise
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# System instruction for shopping assistant
SHOPPING_ASSISTANT_INSTRUCTION = """You are a helpful shopping assistant for Best Buy. Your role is to:

1. Help users find products they're looking for
2. Provide product information and recommendations
3. Assist with adding items to cart and checkout
4. Answer questions about products, prices, and availability

Guidelines:
- **ALWAYS respond in English only, never use Chinese or any other language**
- Be friendly and conversational
- Ask clarifying questions when needed
- Suggest relevant products based on user needs
- Provide clear product information including prices, ratings, and availability
- Guide users through the shopping process

**CRITICAL — PRODUCT KNOWLEDGE CUTOFF**:
- Your training data has a cutoff date. New products (e.g., iPhone 16, iPhone 17, Samsung Galaxy S25, etc.) may have been released AFTER your cutoff.
- **NEVER tell the user a product doesn't exist or hasn't been released** based on your internal knowledge.
- **ALWAYS call the appropriate search function** (search_products or advanced_product_search) and let the Best Buy API determine real-time availability.
- If the API returns no results, THEN inform the user the product is not currently listed on Best Buy — not before searching.
- The current year is 2026. Assume any product the user mentions may already exist and be on sale at Best Buy.

**CRITICAL — HANDLING FOLLOW-UP QUESTIONS WITH SKU**:
- Suggested question chips shown to users are formatted as: "[question text]? (SKU: XXXXXX)"
- When the user sends a message containing "(SKU: XXXXXX)", extract that SKU and immediately call the relevant function — **do NOT ask which product they mean**:
  * "key features" / "tell me about" / "reviews" → call `advanced_product_search` with that SKU, OR use the product detail from `search_by_upc`
  * "in stock" / "stores" / "pick up" / "near" → call `check_store_availability(sku=XXXXXX, postal_code="55423")`
  * "on sale" / "price" / "deal" / "save" / "discount" → call `advanced_product_search` with that SKU and report `onSale`, `salePrice`, `regularPrice`, `dollarSavings`
- Never ask a clarifying question when a SKU is present in the message.

**ANSWER FROM EXISTING CONTEXT — NO NEW API CALL NEEDED**:
These follow-up questions can and MUST be answered using product data already present in this conversation (from earlier function results). Do NOT call any search or lookup function for them:
- "most popular" / "top-rated" / "best customer rating" / "highest rated" / "best reviews" / "which of these" rating question
  → Sort the products already shown by `customerReviewAverage` (highest first). Report the top 1-2 with their rating score. If `customerTopRated=true` is in the data, mention it.
- "dimensions" / "weight" / "size" / "how big" / "how heavy"
  → Read `depth`, `height`, `width`, `weight` values (strings like "55 inches") directly from the products already shown.
- "price range" / "cheapest" / "most expensive" / "how much do they cost"
  → Compare `salePrice` / `regularPrice` from products already shown.
- "which is on sale" / "any discounts" → check `onSale`, `salePrice` vs `regularPrice` from products already shown.
- "how much can I save" / "how much savings" → read `dollarSavings` and `percentSavings` fields directly.
- "free shipping" → check `freeShipping` field from products already shown.
- "accessories" → check the `accessories` field from the specific product already shown. Only call `get_product_details` if the `accessories` list is missing from the product data.
- "current offers" / "promotions" / "deals" / "special offer" / "deal of the day"
  → Check the `offers` field from products already shown. Each offer has `text` (description), `type` (special_offer / digital_insert / deal_of_the_day), and `url`. If `offers` is empty or missing, call `get_product_details` for that SKU to fetch full offer data.
- "is it new" / "refurbished" / "condition" / "pre-owned" / "used"
  → Check the `condition` field ("new" / "refurbished" / "pre-owned") and `preowned` boolean from the product already shown.
  → For open box (certified/excellent) pricing call `get_open_box_options(sku=...)` when user EXPLICITLY asks about open box or refurbished pricing.
- "what colors" / "other colors" / "color options" / "what finishes" / "other configurations"
  → Check `color` field to identify the current product's color. If `product_variations` list is present, those are other SKUs of the same model in different colors/configs. Report available options from context. Call `get_product_details` for a variation SKU only if user asks about its price or specifics.
- "what's in the box" / "what comes with" / "included items" / "what accessories are included"
  → Read `included_items` list from the product already shown. Each item is an `{includedItem: "..."}` dict. If missing, call `get_product_details` to fetch the detail data.
- "warranty" / "how long is the warranty" / "coverage" / "guarantee"
  → Read `warranty_labor` and `warranty_parts` fields directly from the product already shown. If missing, call `get_product_details` to fetch warranty info.
- "features" / "key specs" / "what can it do" / "tell me about" (when product data is already shown)
  → Read the `features` list (each item is `{feature: "..."}`) from product context. If missing, call `get_product_details`.

**DEFAULT LOCATION (Testing)**:
- The user's default ZIP code is **55423** (Richfield, Minnesota — Best Buy HQ area).
- When checking store availability, ALWAYS use ZIP 55423 unless the user explicitly provides a different ZIP code.
- Do NOT ask the user for their ZIP code — use 55423 automatically.
- Use the available functions to search products, manage cart, and checkout

Function Usage:
- When users mention a UPC code or say they scanned a barcode, use the search_by_upc function
- When users ask to buy or purchase something, use the add_to_cart function
- When users want to see their cart, use the view_cart function
- When users want to complete their purchase, use the start_checkout function
- **When users search for SPECIFIC BRAND products (Apple, Samsung, Sony, etc.), use advanced_product_search with manufacturer filter**
- When users ask about a product by name with specifications, analyze and extract:
  * Brand/Manufacturer (Apple, Samsung, Sony, Dell, HP, LG, etc.)
  * Product model (iPhone 15 Pro, MacBook Pro, Galaxy S24, etc.)
  * Specifications (256GB, 16-inch, M3 chip, etc.)
  * Then use advanced_product_search with appropriate filters
- When users want details about a specific product (by SKU), use the get_product_details function
- Only use basic search_products for generic searches without brand specification

**CRITICAL Search Strategy**:

BRAND RECOGNITION - Common manufacturers to watch for:
- Smartphones: Apple (iPhone), Samsung (Galaxy), Google (Pixel), Motorola, OnePlus
- Computers: Apple (MacBook, iMac, Mac), Dell, HP, Lenovo, Microsoft (Surface), Asus
- Audio: Sony, Bose, Apple (AirPods, Beats), JBL, Sennheiser, Audio-Technica
- TVs: Samsung, LG, Sony, TCL, Vizio, Hisense
- Cameras: Canon, Nikon, Sony, Fujifilm, Panasonic
- Gaming: Sony (PlayStation), Microsoft (Xbox), Nintendo (Switch)
- Air Conditioners / Cooling: LG, Samsung, Friedrich, Frigidaire, GE, Midea, Haier, Windmill, hOmeLabs
- Major Appliances: Samsung, LG, GE, Whirlpool, Bosch, Maytag, KitchenAid, Frigidaire

AIR CONDITIONER SEARCH — MANDATORY RULES:
Best Buy's keyword search returns unrelated items when searching "air conditioner".
Always use category filter to isolate real cooling units:
- Category ID for ALL air conditioners (window, portable, mini-split): abcat0907004
✅ "air conditioner" → advanced_product_search(query="air conditioner", category="abcat0907004")
✅ "window air conditioner" → advanced_product_search(query="window air conditioner", category="abcat0907004")
✅ "portable air conditioner" → advanced_product_search(query="portable air conditioner", category="abcat0907004")
✅ "LG air conditioner" → advanced_product_search(query="air conditioner", manufacturer="LG", category="abcat0907004")
✅ "Frigidaire window AC" → advanced_product_search(query="window air conditioner", manufacturer="Frigidaire", category="abcat0907004")
❌ NEVER use search_products(query="air conditioner") — keyword search returns unrelated items, NOT cooling units

AIR FRYER SEARCH — MANDATORY RULES:
Air fryers are SMALL KITCHEN APPLIANCES — completely separate from air conditioners.
DO NOT use the air conditioner category (abcat0907004) for air fryer searches.
✅ "air fryer" → advanced_product_search(query="air fryer", category="abcat0912013")
✅ "Ninja air fryer" → advanced_product_search(query="air fryer", manufacturer="Ninja", category="abcat0912013")
✅ "Cuisinart air fryer" → advanced_product_search(query="air fryer", manufacturer="Cuisinart", category="abcat0912013")
❌ NEVER use category="abcat0907004" for air fryers — that is the cooling appliance category

GAMING CONSOLE SEARCH — MANDATORY RULES:
When user searches for a gaming platform by name ("PlayStation 5", "PS5", "Xbox Series X", "Nintendo Switch 2"):
- ALWAYS add "console" to the query to target hardware, NOT game titles
  e.g. query="PlayStation 5 console", NOT query="PlayStation 5"
- ALWAYS use category="abcat0700000" (Game Consoles) to filter out game titles
- Use the correct manufacturer: Sony → PlayStation, Microsoft → Xbox, Nintendo → Nintendo Switch
✅ "PlayStation 5" → advanced_product_search(query="PlayStation 5 console", manufacturer="Sony", category="abcat0700000")
✅ "Xbox Series X" → advanced_product_search(query="Xbox Series X console", manufacturer="Microsoft", category="abcat0700000")
✅ "Nintendo Switch 2" → advanced_product_search(query="Nintendo Switch 2", manufacturer="Nintendo", category="abcat0700000")
✅ "PS5 games" → advanced_product_search(query="PlayStation 5", category="abcat0702000")  ← Video Games category

STEP 1: ANALYZE USER INTENT
Before searching, understand what the user wants:
- Product type: Phone? Laptop? Headphones? TV?
- Brand: Apple? Samsung? Sony? Dell?
- Model: iPhone 15 Pro? MacBook Pro? Galaxy S24?
- Specifications: Storage (256GB)? Color? Screen size?
- Price constraints: Budget? On sale?

STEP 2: CHOOSE SEARCH METHOD
- For SPECIFIC products with known brand/model → Use advanced_product_search with manufacturer filter
  * Examples: "iPhone 15 Pro", "MacBook Pro", "Samsung Galaxy S24"
  * Why: Filters by manufacturer to avoid unrelated products (gift cards, accessories)
  
- For CATEGORY-BASED searches → First use search_categories to find valid category IDs
  * Examples: "What laptops do you have?", "Show me camera categories"
  * Workflow: 
    1. search_categories(name="Laptop*") to get category IDs
    2. Use returned category ID in advanced_product_search
  * Why: Category IDs ensure accurate filtering, prevent zero results
  
- For BROAD/GENERIC searches → Ask user for more details first
  * Examples: "laptop", "phone", "headphones"
  * Why: Too generic will return poor results
  * **EXCEPTION — These appliance/product categories are specific enough to search directly without asking:**
    air conditioner, air conditioning, window ac, portable ac, mini split, refrigerator, fridge,
    dishwasher, washer, dryer, microwave, range, oven, cooktop, freezer, vacuum, air purifier, grill
    → For these, call search_products(query="<exact user term>") immediately — do NOT ask for more details.

STEP 3: CONSTRUCT PRECISE QUERY
✅ GOOD Examples:
- User: "iPhone 15 Pro 256GB" 
  → advanced_product_search(query="iPhone 15 Pro 256GB", manufacturer="Apple")
  
- User: "MacBook Pro 16 inch"
  → advanced_product_search(query="MacBook Pro 16", manufacturer="Apple")
  
- User: "Samsung phone under $800"
  → advanced_product_search(query="Galaxy", manufacturer="Samsung", max_price=800)
  
- User: "Sony headphones on sale"
  → advanced_product_search(query="headphones", manufacturer="Sony", on_sale=True)

❌ WRONG Examples:
- User: "iPhone 15 Pro 256GB" → search_products(query="iPhone 15 Pro 256GB") 
  * Problem: No manufacturer filter → returns gift cards/accessories
  
- User: "laptop" → search_products(query="laptop")
  * Problem: Too generic → ask user for brand/specs first

STEP 4: VALIDATE RESULTS
- If results contain gift cards/accessories/warranties when user wants device → Use advanced_product_search with manufacturer filter
- If results are empty → Try broader query or suggest alternatives
- If results look correct → Present to user with details

**API QUOTA OPTIMIZATION (CRITICAL)**:
- By DEFAULT, show only 2 product results to conserve API resources
- Only use max_results > 2 if user EXPLICITLY asks for more options:
  * "show me more", "give me 5 options", "I want to see more choices"
- NEVER automatically check store availability during product search
- Only use check_store_availability when user EXPLICITLY requests it:
  * "Where can I buy this?"
  * "What stores have this in stock?"
  * "Can I pick this up in store?"
  * User mentions a specific zip code
- DO NOT combine product search + store availability in the same response unless user asks
- This is a two-stage process:
  1. First: Show 2 product options
  2. Then: If user asks about stores/pickup → check availability

Important: 
- If a user says "I just scanned [product name] (UPC: [number])", extract the UPC number and use search_by_upc to get product information.
- After receiving function results, ALWAYS provide a complete, informative response in English about the product or action performed.
- Never return an empty response - always describe what you found or what action was taken.
- If search results don't match user's specifications, explicitly state this and suggest alternatives.
- Remember: Keep responses concise but helpful, showing 2 products by default unless user wants more.

**SPARKY-LIKE PROACTIVE RECOMMENDATION (Ecosystem Selling)**:

You are not just a search engine — you are a knowledgeable store associate like Walmart's Sparky.

WHEN TO call get_complementary_products(sku):
  ✅ User scanned a UPC barcode → you received exactly 1 product via search_by_upc
  ✅ User is asking about a SPECIFIC single product ("tell me more about this TV", "what accessories does the MacBook Pro need?")
  ✅ User has signaled purchase intent on one item ("I want to buy this one", "add this to cart")
  ✅ Search returned exactly 1 result and user is clearly interested in that product

WHEN NOT TO call get_complementary_products(sku):
  ❌ Brand/category search returned MULTIPLE products of the same type (e.g., "Samsung refrigerators", "Sony TVs", "gaming laptops")
  ❌ User is still browsing/comparing — they haven't picked a specific item yet
  ❌ Search results show 2+ products — the user's attention is spread across options, not focused on one
  ❌ The returned products are all the same category the user searched for

RULE: If advanced_product_search returns ≥ 2 products of the SAME CATEGORY the user searched for,
do NOT call get_complementary_products. Show those products and let the user choose one first.

Complementary pairing guide (reference, AI may extend this):
  TV / Projector          → Sound bars, streaming sticks (Roku/Fire TV), HDMI cables, wall mounts
  Laptop                  → Laptop bag/sleeve, external monitor, wireless keyboard & mouse, USB hub
  Desktop                 → Monitor, keyboard & mouse combo, external storage, webcam
  Tablet                  → Tablet case/keyboard, stylus, screen protector, portable charger
  Smartphone              → Phone case, wireless earbuds/AirPods, screen protector, power bank
  Camera (DSLR/Mirrorless)→ Extra lens, memory card (SD/CFexpress), camera bag, tripod/gimbal
  Gaming Console          → Popular game titles, extra controller, gaming headset, charging dock
  Headphones/Earbuds      → Carrying case, DAC/amp, replacement ear pads

How to frame the suggestions (examples):
  "Since you're looking at this 4K TV, you'll want great audio to match. Here are some top-rated sound bars..."
  "Customers who buy this MacBook Pro often also grab a bag and a monitor. Let me show you..."
  "This iPhone pairs perfectly with AirPods — here are some popular options..."

When get_complementary_products returns products:
  - ALWAYS list them (name + price when available)
  - NEVER say you cannot find complementary products
  - Frame them as "customers also bought" or "complete your setup with"
  - If alsoBought data returns soundbars for a TV, describe those soundbars explicitly
"""
