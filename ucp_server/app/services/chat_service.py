"""
Chat Service
Manages conversation flow and function execution
"""
from typing import Dict, Any, List, Optional
import re
from app.services.gemini_client import GeminiClient
from app.services.bestbuy_client import BestBuyAPIClient
from app.services.cart_service import CartService
from app.services.checkout_service import CheckoutService
from app.schemas.cart import CartItemCreate
from sqlalchemy.orm import Session
import logging
import json

logger = logging.getLogger(__name__)


class ChatService:
    """
    Chat service that orchestrates Gemini AI and UCP Server functions
    """
    
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.bestbuy_client = BestBuyAPIClient()
    
    async def execute_function(
        self,
        function_name: str,
        arguments: Dict[str, Any],
        db: Session,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Execute a function called by Gemini
        
        Args:
            function_name: Name of the function to execute
            arguments: Function arguments
            db: Database session
            user_id: User ID
            
        Returns:
            Function execution result
        """
        try:
            logger.info(f"Executing function: {function_name} with args: {arguments}")
            
            # Product search
            if function_name == "search_products":
                query = arguments.get("query")
                max_results = arguments.get("max_results", 2)  # Reduced default from 5 to 2 to conserve API quota
                
                logger.info(f"Searching products with query: '{query}', max_results: {max_results}")
                
                try:
                    result = await self.bestbuy_client.search_products(query, page_size=max_results)
                    logger.info(f"Best Buy API returned {result.total} products for query: '{query}'")
                    
                    # Format products for AI
                    products = [
                        {
                            "sku": p.sku,
                            "name": p.name,
                            "sale_price": p.sale_price,
                            "regular_price": p.regular_price,
                            "on_sale": p.on_sale,
                            "manufacturer": p.manufacturer,
                            "image": p.image,
                            "customer_top_rated": p.customer_top_rated,
                            "customer_review_average": p.customer_review_average,
                            "free_shipping": p.free_shipping,
                            "depth": p.depth,
                            "height": p.height,
                            "width": p.width,
                            "weight": p.weight,
                            "accessories": p.accessories,
                            "color": p.color,
                            "condition": p.condition,
                            "preowned": p.preowned,
                            "dollar_savings": p.dollar_savings,
                            "percent_savings": p.percent_savings,
                        }
                        for p in result.products
                    ]

                    logger.info(f"Formatted {len(products)} products for AI response")
                    
                    return {
                        "success": True,
                        "products": products,
                        "total_found": result.total
                    }
                except Exception as e:
                    logger.error(f"Error searching products with query '{query}': {e}", exc_info=True)
                    return {
                        "success": False,
                        "error": f"Failed to search products: {str(e)}"
                    }
            
            # Search by UPC
            elif function_name == "search_by_upc":
                upc = arguments.get("upc")
                logger.info(f"Searching for product with UPC: {upc}")
                product = await self.bestbuy_client.search_by_upc(str(upc))
                
                if not product:
                    logger.warning(f"Product not found for UPC: {upc}")
                    return {"success": False, "error": "Product not found with this UPC"}
                
                logger.info(f"Found product: {product.name} (SKU: {product.sku})")
                return {
                    "success": True,
                    "product": {
                        "sku": product.sku,
                        "name": product.name,
                        "price": product.sale_price or product.regular_price,
                        "regular_price": product.regular_price,
                        "sale_price": product.sale_price,
                        "on_sale": product.on_sale,
                        "description": product.short_description or product.long_description,
                        "manufacturer": product.manufacturer,
                        "model_number": product.model_number,
                        "upc": product.upc,
                        "image": product.image,
                        "customer_review_average": product.customer_review_average,
                        "customer_review_count": product.customer_review_count,
                        "free_shipping": product.free_shipping,
                        "in_store_availability": product.in_store_availability,
                        "online_availability": product.online_availability,
                        "color": product.color,
                        "condition": product.condition,
                        "preowned": product.preowned,
                        "depth": product.depth,
                        "height": product.height,
                        "width": product.width,
                        "weight": product.weight,
                        "dollar_savings": product.dollar_savings,
                        "percent_savings": product.percent_savings,
                    }
                }
            
            # Get product details
            elif function_name == "get_product_details":
                sku = arguments.get("sku")
                product = await self.bestbuy_client.get_product_by_sku(str(sku))
                
                if not product:
                    return {"success": False, "error": "Product not found"}
                
                return {
                    "success": True,
                    "product": {
                        "sku": product.sku,
                        "name": product.name,
                        "price": product.sale_price or product.regular_price,
                        "regular_price": product.regular_price,
                        "sale_price": product.sale_price,
                        "on_sale": product.on_sale,
                        "description": product.short_description or product.long_description,
                        "manufacturer": product.manufacturer,
                        "image": product.image,
                        "customer_review_average": product.customer_review_average,
                        "customer_review_count": product.customer_review_count,
                        "color": product.color,
                        "condition": product.condition,
                        "preowned": product.preowned,
                        "depth": product.depth,
                        "height": product.height,
                        "width": product.width,
                        "weight": product.weight,
                        "dollar_savings": product.dollar_savings,
                        "percent_savings": product.percent_savings,
                        "warranty_labor": product.warranty_labor,
                        "warranty_parts": product.warranty_parts,
                        "accessories": product.accessories,
                        "product_variations": product.product_variations,
                        "features": product.features,
                        "included_items": product.included_items,
                        "offers": product.offers,
                    }
                }
            
            # Add to cart
            elif function_name == "add_to_cart":
                sku = str(arguments.get("sku"))
                quantity = arguments.get("quantity", 1)
                
                # Get product details first
                product = await self.bestbuy_client.get_product_by_sku(sku)
                if not product:
                    return {"success": False, "error": "Product not found"}
                
                # Add to cart
                cart_item = CartItemCreate(
                    sku=sku,
                    name=product.name or "Unknown Product",
                    price=product.sale_price or product.regular_price or 0.0,
                    image_url=product.image,
                    quantity=quantity
                )
                
                await CartService.add_item(db, user_id, cart_item)
                
                return {
                    "success": True,
                    "message": f"Added {product.name} to cart",
                    "quantity": quantity
                }
            
            # View cart
            elif function_name == "view_cart":
                cart = await CartService.get_cart(db, user_id)
                
                items = [
                    {
                        "sku": item.sku,
                        "name": item.name,
                        "price": item.price,
                        "quantity": item.quantity,
                        "subtotal": item.subtotal
                    }
                    for item in cart.items
                ]
                
                return {
                    "success": True,
                    "items": items,
                    "total_price": cart.total_price,
                    "item_count": cart.item_count
                }
            
            # Remove from cart
            elif function_name == "remove_from_cart":
                sku = str(arguments.get("sku"))
                removed = await CartService.remove_item(db, user_id, sku)
                
                return {
                    "success": removed,
                    "message": "Item removed from cart" if removed else "Item not found in cart"
                }
            
            # Update cart quantity
            elif function_name == "update_cart_quantity":
                sku = str(arguments.get("sku"))
                quantity = arguments.get("quantity")
                
                item = await CartService.update_quantity(db, user_id, sku, quantity)
                
                return {
                    "success": True,
                    "message": f"Updated quantity to {quantity}"
                }
            
            # Start checkout
            elif function_name == "start_checkout":
                session = await CheckoutService.create_session(db, user_id)
                
                return {
                    "success": True,
                    "session_id": session.id,
                    "total_amount": session.total_amount,
                    "message": "Checkout session created. Please provide shipping information."
                }
            
            # Get recommendations
            elif function_name == "get_product_recommendations":
                sku = str(arguments.get("sku"))
                recommendations = await self.bestbuy_client.get_recommendations(sku)
                
                products = [
                    {
                        "sku": p.sku,
                        "name": p.name,
                        "sale_price": p.sale_price,
                        "regular_price": p.regular_price,
                        "on_sale": p.on_sale,
                        "manufacturer": p.manufacturer,
                        "image": p.image
                    }
                    for p in recommendations[:5]
                ]

                return {
                    "success": True,
                    "recommendations": products
                }
            
            # Check store availability (BOPIS)
            elif function_name == "check_store_availability":
                sku = str(arguments.get("sku"))
                # Default to a central US ZIP when user hasn't provided one
                DEFAULT_POSTAL_CODE = "55423"  # Best Buy HQ area, Richfield MN
                postal_code = arguments.get("postal_code") or DEFAULT_POSTAL_CODE
                radius = arguments.get("radius", 25)
                # Gemini can optionally pass a product_name so we skip an extra API call
                product_name = arguments.get("product_name") or arguments.get("name")

                logger.info(f"Checking store availability for SKU {sku} near {postal_code} (radius: {radius} mi)")

                result = await self.bestbuy_client.get_store_availability(
                    sku=sku,
                    postal_code=postal_code,
                    radius=radius,
                    max_stores=1,           # 2 API calls total: 1 store lookup + 1 availability check
                    product_name=product_name   # avoids an extra API call inside the method
                )
                
                stores = [
                    {
                        "store_name": store.store.name,
                        "address": f"{store.store.address}, {store.store.city}, {store.store.region} {store.store.postal_code}",
                        "distance": store.store.distance,
                        "in_stock": store.in_stock,
                        "pickup_available": store.pickup_available,
                        "phone": store.store.phone
                    }
                    for store in result.stores
                ]
                
                return {
                    "success": True,
                    "product_name": result.product_name,
                    "total_stores": result.total_stores,
                    "stores": stores
                }
            
            # Get also-bought products
            elif function_name == "get_also_bought_products":
                sku = str(arguments.get("sku"))
                also_bought = await self.bestbuy_client.get_also_bought(sku)
                
                products = [
                    {
                        "sku": p.sku,
                        "name": p.name,
                        "sale_price": p.sale_price,
                        "regular_price": p.regular_price,
                        "on_sale": p.on_sale,
                        "manufacturer": p.manufacturer,
                        "image": p.image
                    }
                    for p in also_bought[:5]
                ]
                
                return {
                    "success": True,
                    "also_bought": products,
                    "message": f"Customers who bought this also bought these {len(products)} products"
                }
            
            # Advanced product search
            elif function_name == "advanced_product_search":
                query = arguments.get("query")
                manufacturer = arguments.get("manufacturer")
                category = arguments.get("category")
                min_price = arguments.get("min_price")
                max_price = arguments.get("max_price")
                on_sale = arguments.get("on_sale")
                free_shipping = arguments.get("free_shipping")
                in_store_pickup = arguments.get("in_store_pickup")
                
                logger.info(f"Advanced search: query={query}, manufacturer={manufacturer}, category={category}, price={min_price}-{max_price}")
                
                result = await self.bestbuy_client.advanced_search(
                    query=query,
                    manufacturer=manufacturer,
                    category=category,
                    min_price=min_price,
                    max_price=max_price,
                    on_sale=on_sale,
                    free_shipping=free_shipping,
                    in_store_pickup=in_store_pickup,
                    page_size=5  # Reduced from 10 to 5 to conserve API quota
                )
                
                products = [
                    {
                        "sku": p.sku,
                        "name": p.name,
                        "sale_price": p.sale_price,
                        "regular_price": p.regular_price,
                        "on_sale": p.on_sale,
                        "manufacturer": p.manufacturer,
                        "image": p.image,
                        "customer_top_rated": p.customer_top_rated,
                        "customer_review_average": p.customer_review_average,
                        "free_shipping": p.free_shipping,
                        "depth": p.depth,
                        "height": p.height,
                        "width": p.width,
                        "weight": p.weight,
                        "accessories": p.accessories,
                        "color": p.color,
                        "condition": p.condition,
                        "preowned": p.preowned,
                        "dollar_savings": p.dollar_savings,
                        "percent_savings": p.percent_savings,
                    }
                    for p in result.products
                ]

                return {
                    "success": True,
                    "products": products,
                    "total_found": result.total
                }

            elif function_name == "get_open_box_options":
                sku = arguments.get("sku")
                logger.info(f"Checking open box options for SKU: {sku}")
                result = await self.bestbuy_client.get_open_box_options(str(sku))
                return result

            elif function_name == "search_categories":
                name = arguments.get("name")
                
                logger.info(f"Searching categories: name={name}")
                
                result = await self.bestbuy_client.search_categories(
                    name=name,
                    page_size=20
                )
                
                categories = [
                    {
                        "id": cat.id,
                        "name": cat.name,
                        "url": cat.url,
                        "path": [{"id": p.id, "name": p.name} for p in cat.path] if cat.path else [],
                        "subCategories": [{"id": sc.id, "name": sc.name} for sc in cat.subCategories] if cat.subCategories else []
                    }
                    for cat in result.categories
                ]
                
                return {
                    "success": True,
                    "categories": categories,
                    "total_found": result.total,
                    "message": f"Found {result.total} categories matching '{name}'. Use the 'id' field (e.g., 'abcat0502000') in advanced_product_search for filtering."
                }

            # ── Sparky-like complementary product recommendations ─────────────
            elif function_name == "get_complementary_products":
                sku = str(arguments.get("sku"))
                # category_hints may be injected by proactive path or by Gemini args
                category_hints = arguments.get("category_hints") or []
                manufacturer_hint = arguments.get("manufacturer_hint") or None
                logger.info(
                    f"Getting complementary products for SKU: {sku}, "
                    f"category_hints={category_hints}, manufacturer_hint={manufacturer_hint}"
                )

                complementary = await self.bestbuy_client.get_complementary_products(
                    sku,
                    category_hints=category_hints,
                    manufacturer_hint=manufacturer_hint,
                )

                products = [
                    {
                        "sku": p.sku,
                        "name": p.name,
                        "sale_price": p.sale_price,
                        "regular_price": p.regular_price,
                        "on_sale": p.on_sale,
                        "manufacturer": p.manufacturer,
                        "image": p.image
                    }
                    for p in complementary[:6]  # up to 6 complementary picks
                ]

                return {
                    "success": True,
                    "products": products,
                    "message": (
                        f"✅ Found {len(products)} complementary products for SKU {sku} — "
                        "present ALL of them to the user as ecosystem suggestions. "
                        "Do NOT say you have no recommendations. "
                        "List each product name and price in your response."
                    )
                }

            else:
                return {
                    "success": False,
                    "error": f"Unknown function: {function_name}"
                }
                
        except Exception as e:
            logger.error(f"Error executing function {function_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process_message(
        self,
        message: str,
        db: Session,
        user_id: str,
        conversation_history: List[Dict[str, str]] = None,
        user_context=None
    ) -> Dict[str, Any]:
        """
        Process user message with Gemini and execute functions
        
        Args:
            message: User's message
            db: Database session
            user_id: User ID
            conversation_history: Previous conversation
            user_context: Optional UserBehaviorContext for personalized recommendations
            
        Returns:
            Response with AI message and function results
        """
        try:
            # Build (optionally personalized) system instruction
            system_instruction = self.gemini_client.build_system_instruction(user_context)
            if user_context and user_context.interaction_count > 0:
                logger.info(
                    f"Personalized context injected: categories={user_context.recent_categories}, "
                    f"brands={user_context.favorite_manufacturers}, "
                    f"interactions={user_context.interaction_count}"
                )

            # ── Proactive accessory pre-fetch ──────────────────────────────────────
            # When user's message expresses accessory/complement intent and we have
            # a recently-viewed SKU, execute get_complementary_products() immediately
            # WITHOUT waiting for Gemini to decide — inject the real products into
            # the system instruction so Gemini always describes real items.
            proactive_products = []
            if (
                user_context
                and user_context.recent_skus
                and self._is_accessory_intent(message)
            ):
                anchor_sku = user_context.recent_skus[0]
                cat_hints   = user_context.recent_categories or []
                mfr_hint    = user_context.favorite_manufacturers[0] if user_context.favorite_manufacturers else None
                logger.info(
                    f"🛍️  Proactive accessory fetch: SKU={anchor_sku}, "
                    f"categories={cat_hints}, manufacturer={mfr_hint}"
                )
                try:
                    comp_result = await self.execute_function(
                        function_name="get_complementary_products",
                        arguments={
                            "sku": anchor_sku,
                            "category_hints": cat_hints,
                            "manufacturer_hint": mfr_hint,
                        },
                        db=db,
                        user_id=user_id
                    )
                    if comp_result.get("success") and comp_result.get("products"):
                        proactive_products = comp_result["products"]
                        logger.info(f"  Pre-fetched {len(proactive_products)} complementary products")
                        # Inject product names+prices into system instruction so Gemini presents them
                        product_lines = []
                        for p in proactive_products[:5]:
                            name = p.get("name", "Unknown")
                            price = p.get("regularPrice") or p.get("salePrice") or "N/A"
                            sku = p.get("sku", "")
                            product_lines.append(f"  • {name} (SKU {sku}) — ${price}")
                        injection = (
                            f"\n\n{'═'*70}\n"
                            f"PRE-FETCHED COMPLEMENTARY PRODUCTS (real Best Buy inventory) for SKU {anchor_sku}:\n"
                            + "\n".join(product_lines) + "\n"
                            f"INSTRUCTION: The user is asking about accessories. Present the above products "
                            f"positively by name and price. Do NOT say you have no recommendations.\n"
                            f"Do NOT call get_complementary_products again — products already loaded above.\n"
                            f"{'═'*70}"
                        )
                        system_instruction += injection
                except Exception as e:
                    logger.warning(f"  Proactive fetch failed: {e}")
            # ────────────────────────────────────────────────────────────────────────

            # ── Proactive SKU detail pre-fetch ────────────────────────────────────
            # When the user's message explicitly contains a SKU (e.g. from a suggestion
            # chip like "What are the dimensions of X? (SKU: 6578065)"), fetch the full
            # product detail BEFORE calling Gemini so it has height/depth/weight/etc.
            # Without this, Gemini only sees the slim `advanced_search` cached data
            # which often lacks dimension fields.
            sku_in_message = re.findall(r'\bSKU[:\s#]+(\d{6,8})\b', message, re.IGNORECASE)
            if sku_in_message:
                detail_sku = sku_in_message[0]
                try:
                    detail_product = await self.bestbuy_client.get_product_by_sku(detail_sku)
                    if detail_product:
                        dim_parts = []
                        # Standard top-level fields first
                        if detail_product.height: dim_parts.append(f"Height: {detail_product.height}")
                        if detail_product.width:  dim_parts.append(f"Width: {detail_product.width}")
                        if detail_product.depth:  dim_parts.append(f"Depth: {detail_product.depth}")
                        if detail_product.weight: dim_parts.append(f"Weight: {detail_product.weight}")
                        # Supplement from details[] collection (e.g. "Product Height With Stand": "41.7 inches")
                        if detail_product.details:
                            for d in detail_product.details:
                                dname = (d.get('name') or '').strip()
                                dval  = (d.get('value') or '').strip()
                                if dval and any(kw in dname.lower() for kw in ['height', 'depth', 'width', 'weight', 'dimension']):
                                    entry = f"{dname}: {dval}"
                                    if entry not in dim_parts:
                                        dim_parts.append(entry)
                        dim_text = "\n    ".join(dim_parts) if dim_parts else "Not available"
                        color_text   = detail_product.color or "Not available"
                        wl_text      = detail_product.warranty_labor or "Not available"
                        wp_text      = detail_product.warranty_parts or "Not available"
                        rating_text  = (
                            f"{detail_product.customer_review_average} ({detail_product.customer_review_count} reviews)"
                            if detail_product.customer_review_average else "Not available"
                        )
                        price_text = (
                            f"${detail_product.sale_price} (on sale, was ${detail_product.regular_price})"
                            if detail_product.on_sale else f"${detail_product.regular_price or detail_product.sale_price}"
                        )
                        injection = (
                            f"\n\n{'═'*70}\n"
                            f"FULL PRODUCT DETAIL for SKU {detail_sku} ({detail_product.name}):\n"
                            f"  Price: {price_text}\n"
                            f"  Dimensions & Weight: {dim_text}\n"
                            f"  Color: {color_text}\n"
                            f"  Customer Rating: {rating_text}\n"
                            f"  Warranty (Labor): {wl_text}\n"
                            f"  Warranty (Parts): {wp_text}\n"
                            f"INSTRUCTION: Use ONLY the data above to answer the user's question. "
                            f"Do NOT say dimensions are unavailable if they appear above.\n"
                            f"{'═'*70}"
                        )
                        system_instruction += injection
                        logger.info(f"SKU detail pre-fetch: injected full data for SKU {detail_sku} — dims: {dim_text}")
                except Exception as e:
                    logger.warning(f"SKU detail pre-fetch failed for SKU {detail_sku}: {e}")
            # ─────────────────────────────────────────────────────────────────────────

            # Call Gemini
            gemini_response = await self.gemini_client.chat(
                message=message,
                conversation_history=conversation_history,
                system_instruction=system_instruction
            )
            
            # Extract response
            ai_message = gemini_response.get("message", "")
            function_calls = gemini_response.get("function_calls", [])
            
            logger.info(f"Gemini initial response - message: '{ai_message}', function_calls: {len(function_calls)}")
            
            # Execute function calls
            function_results = []
            all_products = list(proactive_products)  # seed with proactively fetched products
            
            for func_call in function_calls:
                logger.info(f"Executing function: {func_call['name']} with args: {func_call['arguments']}")
                result = await self.execute_function(
                    function_name=func_call["name"],
                    arguments=func_call["arguments"],
                    db=db,
                    user_id=user_id
                )
                logger.info(f"Function {func_call['name']} result: {result}")
                function_results.append({
                    "function": func_call["name"],
                    "result": result
                })
                
                # Collect products from search results
                if result.get("success") and "products" in result:
                    products_data = result["products"]
                    logger.info(f"Collected {len(products_data)} products from {func_call['name']}")
                    all_products.extend(products_data)
                # Collect single product from detailed searches
                elif result.get("success") and "product" in result:
                    product_data = result["product"]
                    logger.info(f"Collected 1 product from {func_call['name']}: {product_data.get('name')}")
                    all_products.append(product_data)
            
            # If there are function calls, enter a multi-round function calling loop
            # Gemini may chain multiple rounds (e.g. search → get_complementary_products → final text)
            if function_calls:
                try:
                    if conversation_history is None:
                        conversation_history = []

                    # Updated history: user message + model's initial (possibly empty) message
                    updated_history = conversation_history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": ai_message or ""}
                    ]

                    # We allow up to MAX_ROUNDS extra Gemini calls to resolve chained function calls
                    MAX_ROUNDS = 3
                    rounds = 0
                    pending_calls = function_calls  # start with first-round calls already executed

                    while pending_calls and rounds < MAX_ROUNDS:
                        rounds += 1
                        logger.info(f"=== Function calling round {rounds}: {len(pending_calls)} call(s) pending ===")

                        # Execute pending function calls and collect results/products
                        round_results = []
                        for func_call in pending_calls:
                            logger.info(f"  Executing: {func_call['name']} {func_call['arguments']}")
                            if rounds > 1:
                                # First round already executed above; only execute from round 2+
                                result = await self.execute_function(
                                    function_name=func_call["name"],
                                    arguments=func_call["arguments"],
                                    db=db,
                                    user_id=user_id
                                )
                                function_results.append({"function": func_call["name"], "result": result})
                                if result.get("success") and "products" in result:
                                    all_products.extend(result["products"])
                                    logger.info(f"  Collected {len(result['products'])} products from {func_call['name']}")
                                elif result.get("success") and "product" in result:
                                    all_products.append(result["product"])
                            else:
                                # Round 1 results already in function_results list
                                result = next(
                                    (fr["result"] for fr in function_results if fr["function"] == func_call["name"]),
                                    {}
                                )

                            round_results.append({"name": func_call["name"], "response": {"result": result}})

                        # Send all round results back to Gemini
                        logger.info(f"  Sending {len(round_results)} result(s) back to Gemini (round {rounds})")
                        gemini_resp = await self.gemini_client.chat(
                            conversation_history=updated_history,
                            function_responses=round_results,
                            system_instruction=system_instruction
                        )

                        ai_message = gemini_resp.get("message", "")
                        pending_calls = gemini_resp.get("function_calls", [])

                        logger.info(f"  Gemini round-{rounds} response: message='{ai_message[:80]}', "
                                    f"next_function_calls={[f['name'] for f in pending_calls]}")

                        # Append this exchange to updated_history for the next round
                        # (empty assistant content signals function-call turn, then user function result turn)
                        # (No need to be exact here; Gemini just needs continuity)

                    if pending_calls:
                        logger.warning(f"Stopped after {MAX_ROUNDS} rounds; {len(pending_calls)} calls still pending")

                    logger.info(f"Multi-round function calling finished. Final message length: {len(ai_message)}")

                except Exception as e:
                    logger.error(f"Error in function calling loop: {e}", exc_info=True)
                    ai_message = f"I found the product information, but encountered an error generating the response: {str(e)}"
            
            # Only return function_calls if we didn't complete the Function Calling flow
            # If we completed the flow, the final ai_message contains the complete response
            return_function_calls = [] if function_calls and ai_message else function_calls
            
            # Deduplicate products by SKU and limit to 8 (primary + complementary)
            seen = set()
            deduped_products = []
            for p in all_products:
                sku = str(p.get("sku", ""))
                if sku and sku not in seen:
                    seen.add(sku)
                    deduped_products.append(p)
            display_products = deduped_products[:8]

            # ── SKU-focus logic ───────────────────────────────────────────────
            # When Gemini answers a suggestion question (e.g. "Which has best
            # rating?"), it replies in plain text calling out a specific SKU.
            # In that case we want to show ONLY that product card so the user
            # gets a focused card + targeted follow-up questions.
            #
            # Rules:
            #  1. Extract any explicit "SKU: XXXXXXX" mentions from ai_message.
            #  2. If the AI calls out 1-2 specific SKUs:
            #     a. Try to find them in display_products (already fetched).
            #     b. If not there, fetch via get_product_by_sku (detail endpoint).
            #     c. Replace display_products with ONLY those SKUs.
            #  3. If no explicit SKU found → keep display_products as-is.
            # ─────────────────────────────────────────────────────────────────
            if ai_message:
                # Pattern matches "SKU: 6505534" / "(SKU: 6505534)" / "SKU 6505534"
                sku_matches = re.findall(r'\bSKU[:\s#]+(\d{6,8})\b', ai_message, re.IGNORECASE)
                unique_skus = list(dict.fromkeys(sku_matches))[:2]   # max 2, preserve order

                if unique_skus:
                    # Build a lookup of already-fetched products by SKU string
                    existing_by_sku = {str(p.get("sku", "")): p for p in display_products}
                    focused: list = []

                    for sku in unique_skus:
                        if sku in existing_by_sku:
                            focused.append(existing_by_sku[sku])
                            logger.info(f"SKU focus: using cached product for SKU {sku}")
                        else:
                            # Not in current list — fetch the detail page
                            try:
                                product = await self.bestbuy_client.get_product_by_sku(sku)
                                if product:
                                    focused.append({
                                        "sku": product.sku,
                                        "name": product.name,
                                        "sale_price": product.sale_price,
                                        "regular_price": product.regular_price,
                                        "on_sale": product.on_sale,
                                        "manufacturer": product.manufacturer,
                                        "image": product.image,
                                        "medium_image": product.medium_image,
                                        "thumbnail_image": product.thumbnail_image,
                                        "customer_top_rated": product.customer_top_rated,
                                        "customer_review_average": product.customer_review_average,
                                        "customer_review_count": product.customer_review_count,
                                        "free_shipping": product.free_shipping,
                                        "depth": product.depth,
                                        "height": product.height,
                                        "width": product.width,
                                        "weight": product.weight,
                                        "accessories": product.accessories,
                                        "color": product.color,
                                        "condition": product.condition,
                                        "preowned": product.preowned,
                                        "dollar_savings": product.dollar_savings,
                                        "percent_savings": product.percent_savings,
                                    })
                                    logger.info(f"SKU focus: fetched '{product.name}' (SKU {sku})")
                            except Exception as e:
                                logger.warning(f"SKU focus: failed to fetch SKU {sku}: {e}")

                    if focused:
                        display_products = focused
                        logger.info(f"SKU focus: narrowed display_products to {[p.get('name','?')[:50] for p in focused]}")
            # ─────────────────────────────────────────────────────────────────
            logger.info(f"Final message preview: '{ai_message[:200]}...'" if len(ai_message) > 200 else f"Final message: '{ai_message}'")
            
            if display_products:
                logger.info(f"Products to display: {[p.get('name', 'Unknown')[:50] for p in display_products]}")

            # Generate AI-powered follow-up question chips when products are present
            suggested_questions = []
            if display_products:
                suggested_questions = await self._generate_suggested_questions(
                    user_message=message,
                    products=display_products
                )
            
            return {
                "message": ai_message,
                "function_calls": return_function_calls,
                "function_results": function_results,
                "products": display_products,
                "suggested_questions": suggested_questions
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "message": "Sorry, I encountered an error processing your request.",
                "error": str(e)
            }
    
    async def _generate_suggested_questions(
        self,
        user_message: str,
        products: list,
        max_questions: int = 3
    ) -> List[str]:
        """
        Generate generic, data-driven follow-up question chips based on the
        entire products list — NOT tied to a single SKU.

        Question pool (picked dynamically based on actual product data):
          1.  Most popular / top-rated       → customerTopRated / customerReviewAverage
          2.  Biggest discount               → regularPrice - salePrice
          --- SINGLE PRODUCT ---
          3a. Color / variation options      → productVariations list (other SKU configs)
          3b. Dimensions / weight            → depth/height/width/weight from context
          4.  Open box / refurbished         → triggers get_open_box_options
          5.  What's included in the box     → includedItemList from detail API
          6.  Warranty information           → warrantyLabor/warrantyParts from detail API
          --- MULTIPLE PRODUCTS ---
          3c. Category-specific spec (audio) → Wired or wireless variants?  [BEFORE TV check]
          3c. Category-specific spec (TV)    → Other screen size options?
          3c. Category-specific spec (appl.) → Other capacity options?
          3c. Category-specific spec (laptop)→ Other screen size / storage configs?
          3c. Category-specific spec (other) → Other configurations or sizes?
          4.  Color options                  → color field from multiple products
          --- COMMON ---
          7.  Special offers / promotions    → offers field + dollarSavings from context
          8.  Accessories                    → accessories list from Best Buy API
          9.  Current on-sale items          → onSale == True count
         10.  Price range                    → spread between cheapest & most expensive
         11.  Free-shipping options          → freeShipping == True
        Note: in-store pickup questions are excluded — they trigger slow BOPIS calls.
        Priority: questions that are backed by real data come first.
        """
        if not products:
            return []

        # ---------- analyse the product list ----------
        # Top-rated: customerTopRated = True, or highest customerReviewAverage
        top_rated = [
            p for p in products
            if p.get('customer_top_rated') or p.get('customerTopRated')
        ]
        rated_products = [
            p for p in products
            if p.get('customer_review_average') or p.get('customerReviewAverage')
        ]
        best_rated = None
        if rated_products:
            best_rated = max(
                rated_products,
                key=lambda p: float(p.get('customer_review_average') or p.get('customerReviewAverage') or 0)
            )

        # Biggest discount (absolute dollar savings)
        best_deal = None
        best_savings = 0.0
        for p in products:
            reg = p.get('regular_price') or p.get('regularPrice')
            sale = p.get('sale_price') or p.get('salePrice')
            try:
                if reg and sale and float(reg) > float(sale):
                    savings = float(reg) - float(sale)
                    if savings > best_savings:
                        best_savings = savings
                        best_deal = p
            except (TypeError, ValueError):
                pass

        # On-sale count
        on_sale_count = sum(
            1 for p in products
            if p.get('on_sale') or p.get('onSale')
        )

        # Color variety
        colors = set()
        for p in products:
            c = p.get('color')
            if c:
                colors.add(c.strip().lower())

        # Has dimension data (depth / height / width / weight)
        has_dimensions = any(
            p.get('depth') or p.get('height') or p.get('width') or p.get('weight')
            for p in products
        )

        # Has accessories data
        has_accessories = any(
            p.get('accessories') for p in products
        )

        # Free shipping
        free_ship_count = sum(
            1 for p in products
            if p.get('free_shipping') or p.get('freeShipping')
        )

        # Has current special offers / promotions (from offers field or prominent savings)
        has_offers = any(
            p.get('offers') for p in products
        )
        has_savings_data = best_savings > 5.0  # only highlight if savings > $5

        # Has condition data flagging refurbished / pre-owned products
        has_condition_info = any(
            p.get('condition') and p.get('condition', '').lower() != 'new'
            for p in products
        )

        # Has product variation data (other colors / configs) — from detail endpoint
        has_variations = any(
            p.get('product_variations') for p in products
        )

        # Has warranty information
        has_warranty = any(
            p.get('warranty_labor') or p.get('warranty_parts')
            for p in products
        )

        # Has "what's in the box" data
        has_included_items = any(
            p.get('included_items') for p in products
        )

        # Has product features list
        has_features = any(
            p.get('features') for p in products
        )

        # Price range
        prices = []
        for p in products:
            price = p.get('sale_price') or p.get('salePrice') or \
                    p.get('regular_price') or p.get('regularPrice')
            try:
                if price:
                    prices.append(float(price))
            except (TypeError, ValueError):
                pass

        # Derive a short search topic from user_message (≤ 3 content words).
        # Strip common question-word prefixes first so that when the user taps a
        # suggested question as their next message the topic stays clean.
        # e.g. "Which Wifi router has the biggest discount?" → "Wifi router"
        #      "Are any LG refrigerator models on sale?"    → "LG refrigerator"
        _Q_PREFIX = re.compile(
            r'^(?:which|are\s+(?:any\s+)?(?:there\s+)?|can\s+i(?:\s+buy|\s+get)?'
            r'|what(?:\s+is|\s+are|\s+color|\s+\'s)?|do\s+any(?:\s+of\s+these)?'
            r'|is\s+(?:the|any)|how(?:\s+much|\s+many)?)\s+',
            re.IGNORECASE
        )
        _STOP_AT = {
            'has', 'have', 'is', 'are', 'be', 'come', 'comes',
            'options', 'models', 'model', 'option', 'currently',
            'available', 'right', 'now', 'with', 'between',
        }
        cleaned = _Q_PREFIX.sub('', user_message.strip())
        topic_parts: List[str] = []
        for raw in cleaned.split():
            w = raw.strip('?.,!').lower()
            if not w:
                continue
            if w in _STOP_AT:
                break
            topic_parts.append(raw.strip('?.,!'))
            if len(topic_parts) >= 3:
                break
        topic = " ".join(topic_parts) if topic_parts else "these products"

        # Override topic with real product names so suggestions are always meaningful.
        # A topic derived from the user message can be a single pronoun (e.g. "I", "it")
        # or fragment when the user asks a follow-up on an already-found product.
        _single_product = len(products) == 1  # pre-compute for topic override & later use
        if _single_product:
            _pname = (products[0].get('name') or '').strip()
            if _pname:
                # Strip trailing carrier / variant in parentheses: "iPhone 17 (AT&T)" → "iPhone 17"
                _pname_clean = re.sub(r'\s*\([^)]*\)\s*$', '', _pname).strip()
                # Strip leading "Manufacturer - " prefix: "Apple - iPhone 17" → "iPhone 17"
                _pname_clean = re.sub(r'^[^-]+-\s*', '', _pname_clean).strip()
                # Limit to 45 chars, break at last space
                if len(_pname_clean) > 45:
                    _pname_clean = _pname_clean[:45].rsplit(' ', 1)[0]
                topic = _pname_clean if _pname_clean else _pname[:45]
        else:
            # For multi-product, protect against degenerate topics (pronouns / single letters)
            _bad_topic = len(topic) < 3 or topic.lower() in {
                'i', 'it', 'me', 'we', 'the', 'a', 'an', 'these', 'those', 'this', 'that'
            }
            if _bad_topic:
                _manufacturers = list({
                    (p.get('manufacturer') or '').strip()
                    for p in products
                    if p.get('manufacturer')
                })
                if len(_manufacturers) == 1 and _manufacturers[0]:
                    topic = _manufacturers[0]
                else:
                    topic = "these products"

        # ---------- detect product category from topic + product names ----------
        _all_text = (user_message + " " + " ".join(
            p.get('name', '') for p in products
        )).lower()

        _is_tv_monitor = any(w in _all_text for w in [
            'tv', 'television', 'monitor', 'display', 'oled', 'qled', 'screen',
            'inch class', '" class', 'class led', 'class oled', 'class qled'
        ])
        _is_appliance = any(w in _all_text for w in [
            'refrigerator', 'fridge', 'washer', 'dryer', 'dishwasher',
            'microwave', 'range', 'oven', 'cooktop', 'freezer', 'cu. ft'
        ])
        _is_laptop_tablet = any(w in _all_text for w in [
            'laptop', 'macbook', 'notebook', 'chromebook', 'tablet', 'ipad',
            'surface pro', 'inch laptop', '" laptop'
        ])
        _is_audio = any(w in _all_text for w in [
            'headphone', 'earphone', 'earbud', 'airpod', 'speaker',
            'soundbar', 'sound bar', 'headset'
        ])

        # ---------- build the question pool (ordered by relevance) ----------
        pool: List[str] = []

        # ── SINGLE PRODUCT ──────────────────────────────────────────────────────
        # Product card already shows: ★ rating, sale badge, price, savings amount.
        # So skip "rating" and "on sale?" questions — they're redundant.
        # Instead surface deeper purchase-decision info the user can't see at a glance.
        if _single_product:
            _dim_keywords = [
                'dimension', 'weight', 'height', 'width', 'depth',
                'size', 'how big', 'how heavy', 'measurements'
            ]
            _warranty_keywords = ['warrant', 'guarantee', 'coverage']
            _open_box_keywords = ['open box', 'refurb', 'pre-owned', 'preowned', 'used', 'second hand']
            _color_keywords = ['color', 'colour', 'finish', 'variant', 'configuration']
            _included_keywords = ["what's included", "in the box", "comes with", "included"]

            _already_asked_dims     = any(kw in user_message.lower() for kw in _dim_keywords)
            _already_asked_warranty = any(kw in user_message.lower() for kw in _warranty_keywords)
            _already_asked_openbox  = any(kw in user_message.lower() for kw in _open_box_keywords)
            _already_asked_color    = any(kw in user_message.lower() for kw in _color_keywords)
            _already_asked_included = any(kw in user_message.lower() for kw in _included_keywords)

            # SQ1: Warranty — most valuable for high-ticket electronics/appliances
            if not _already_asked_warranty:
                pool.append(f"What warranty does the {topic} come with?")

            # SQ2: Color / other configurations
            if not _already_asked_color:
                if has_variations:
                    pool.append(
                        f"Are there other colors or configurations available for the {topic}?"
                    )
                else:
                    pool.append(
                        f"Does the {topic} come in other colors or finish options?"
                    )

            # SQ3: Open box / refurbished / pre-owned
            if not _already_asked_openbox:
                pool.append(
                    f"Are there open box, refurbished, or pre-owned versions of the {topic} available at a lower price?"
                )

            # SQ4: Dimensions / weight (skip if user just asked this)
            if not _already_asked_dims:
                pool.append(f"What are the dimensions and weight of the {topic}?")

            # SQ5: What's included in the box
            if not _already_asked_included:
                if has_included_items:
                    pool.append(f"What comes in the box with the {topic}?")
                else:
                    pool.append(f"What's included in the box with the {topic}?")

            # SQ6: Accessories
            if has_accessories:
                pool.append(f"What accessories are compatible with the {topic}?")
            else:
                pool.append(f"Are there recommended accessories for the {topic}?")

            # SQ7: Special offers (only when explicit offers data present — not visible on card)
            if has_offers:
                pool.append(
                    f"What current special offers or deals are available for the {topic}?"
                )

        # ── MULTIPLE PRODUCTS ───────────────────────────────────────────────────
        else:
            # MQ1: Rating / popularity
            if best_rated:
                pool.append(f"Which of these {topic} has the best customer rating?")
            else:
                pool.append(f"Which of these {topic} is the most popular?")

            # MQ2: Biggest discount
            if best_deal and best_savings > 0:
                pool.append(f"Which {topic} has the biggest discount right now?")

            # MQ3: Category-specific spec comparison (check audio before TV to avoid false positive)
            if _is_audio:
                pool.append(f"Are there wired or wireless variants of the {topic}?")
            elif _is_tv_monitor:
                pool.append(f"Are there other screen size options for the {topic}?")
            elif _is_appliance:
                pool.append(f"Are there other capacity or size options for the {topic}?")
            elif _is_laptop_tablet:
                pool.append(f"Are there other screen size or storage configurations for the {topic}?")
            else:
                pool.append(f"Are there other configurations or sizes available for {topic}?")

            # MQ4: Color options
            if len(colors) >= 2:
                pool.append(f"What color or finish options are available for {topic}?")
            elif len(products) >= 2:
                pool.append(f"Are there different color or finish options for {topic}?")

            # MQ5: Current special offers / promotions
            if has_offers:
                pool.append(f"What current special offers or deals are available for the {topic}?")
            elif has_savings_data or on_sale_count > 0:
                pool.append(f"Are there any current promotional offers or discounts on {topic}?")
            else:
                pool.append(f"Are there any current special offers or deals on {topic}?")

            # MQ6: Accessories
            if has_accessories:
                pool.append(f"What accessories are compatible with the {topic}?")
            else:
                pool.append(f"Are there recommended accessories for the {topic}?")

            # MQ7: Are any on sale?
            if on_sale_count > 0 and on_sale_count < len(products):
                pool.append(f"Which {topic} options are currently on sale?")
            elif on_sale_count == 0:
                pool.append(f"Are any {topic} models currently on sale or discounted?")

            # MQ8: Price range
            if len(prices) >= 2:
                low, high = min(prices), max(prices)
                if high > low:
                    pool.append(
                        f"What is the price range for {topic} — from ${low:,.0f} to ${high:,.0f}?"
                    )

            # MQ9: Free shipping
            if free_ship_count > 0:
                pool.append(f"Do any of these {topic} options come with free shipping?")

        # Deduplicate and return top N
        seen: set = set()
        result: List[str] = []
        for q in pool:
            if q not in seen:
                seen.add(q)
                result.append(q)
            if len(result) >= max_questions:
                break

        # For single-product responses, append "(SKU: XXXXX)" to each question so
        # that Gemini can immediately resolve the product without asking the user.
        # The system prompt already knows to extract and use the SKU from this suffix.
        if _single_product:
            sku = str(products[0].get('sku') or products[0].get('SKU') or '').strip()
            if sku:
                result = [f"{q} (SKU: {sku})" for q in result]

        return result

    def _is_accessory_intent(self, message: str) -> bool:
        """
        Return True if the user's message expresses intent to find accessories,
        complementary items, or ecosystem products for something they've already viewed.
        """
        msg = message.lower()
        ACCESSORY_KEYWORDS = [
            "accessories", "accessory", "what else", "what should i get",
            "goes with", "go with", "pair with", "pairs with",
            "complement", "complete my setup", "complete the setup",
            "what accessories", "for it", "for this", "for that",
            "what other", "anything else", "also need", "also want",
            "soundbar", "mount", "cable", "case", "bag", "stand",
            "enhance", "upgrade", "add to", "bundle",
        ]
        return any(kw in msg for kw in ACCESSORY_KEYWORDS)

    def _format_function_results(self, function_results: List[Dict[str, Any]]) -> str:
        """
        Format function execution results for Gemini
        
        Args:
            function_results: List of function execution results
            
        Returns:
            Formatted text describing the results
        """
        formatted_parts = []
        
        for func_result in function_results:
            func_name = func_result["function"]
            result = func_result["result"]
            
            if result.get("success"):
                if func_name == "search_by_upc":
                    product = result.get("product", {})
                    formatted_parts.append(
                        f"Found product: {product.get('name')} "
                        f"(SKU: {product.get('sku')}, Price: ${product.get('price')}, "
                        f"Rating: {product.get('customer_review_average')}/5 from {product.get('customer_review_count')} reviews)"
                    )
                elif func_name == "search_products":
                    products = result.get("products", [])
                    formatted_parts.append(f"Found {len(products)} products")
                elif func_name == "add_to_cart":
                    formatted_parts.append(result.get("message", "Item added to cart"))
                elif func_name == "view_cart":
                    items = result.get("items", [])
                    total = result.get("total_price", 0)
                    formatted_parts.append(f"Cart has {len(items)} items, total: ${total}")
                else:
                    formatted_parts.append(f"{func_name} executed successfully")
            else:
                error = result.get("error", "Unknown error")
                formatted_parts.append(f"{func_name} failed: {error}")
        
        return "Function execution results:\n" + "\n".join(formatted_parts)
