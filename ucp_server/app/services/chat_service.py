"""
Chat Service
Manages conversation flow and function execution
"""
from typing import Dict, Any, List, Optional
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
                            "price": p.sale_price or p.regular_price,
                            "on_sale": p.on_sale,
                            "image": p.image
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
                        "online_availability": product.online_availability
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
                        "image": product.image
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
                        "price": p.sale_price or p.regular_price
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
                postal_code = arguments.get("postal_code")
                radius = arguments.get("radius", 25)
                
                logger.info(f"Checking store availability for SKU {sku} near {postal_code or 'all locations'}")
                
                result = await self.bestbuy_client.get_store_availability(
                    sku=sku,
                    postal_code=postal_code,
                    radius=radius,
                    max_stores=3  # Reduced to minimize API calls and avoid quota issues
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
                        "price": p.sale_price or p.regular_price,
                        "on_sale": p.on_sale,
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
                        "price": p.sale_price or p.regular_price,
                        "regular_price": p.regular_price,
                        "on_sale": p.on_sale,
                        "manufacturer": p.manufacturer,
                        "image": p.image
                    }
                    for p in result.products
                ]
                
                return {
                    "success": True,
                    "products": products,
                    "total_found": result.total
                }
            
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
                        "price": p.sale_price or p.regular_price,
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
            
            logger.info(f"Returning response - message length: {len(ai_message)}, function_calls: {len(return_function_calls)}, function_results: {len(function_results)}, products: {len(display_products)}")
            logger.info(f"Final message preview: '{ai_message[:200]}...'" if len(ai_message) > 200 else f"Final message: '{ai_message}'")
            
            if display_products:
                logger.info(f"Products to display: {[p.get('name', 'Unknown')[:50] for p in display_products]}")
            
            return {
                "message": ai_message,
                "function_calls": return_function_calls,
                "function_results": function_results,
                "products": display_products  # Add products to response
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "message": "Sorry, I encountered an error processing your request.",
                "error": str(e)
            }
    
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
