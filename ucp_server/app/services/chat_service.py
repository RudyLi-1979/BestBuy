"""
Chat Service
Manages conversation flow and function execution
"""
from typing import Dict, Any, List, Optional
from app.services.gemini_client import GeminiClient, SHOPPING_ASSISTANT_INSTRUCTION
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
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Process user message with Gemini and execute functions
        
        Args:
            message: User's message
            db: Database session
            user_id: User ID
            conversation_history: Previous conversation
            
        Returns:
            Response with AI message and function results
        """
        try:
            # Call Gemini
            gemini_response = await self.gemini_client.chat(
                message=message,
                conversation_history=conversation_history,
                system_instruction=SHOPPING_ASSISTANT_INSTRUCTION
            )
            
            # Extract response
            ai_message = gemini_response.get("message", "")
            function_calls = gemini_response.get("function_calls", [])
            
            logger.info(f"Gemini initial response - message: '{ai_message}', function_calls: {len(function_calls)}")
            
            # Execute function calls
            function_results = []
            all_products = []  # Collect all products from function results
            
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
            
            # If there are function calls, send results back to Gemini for final response
            if function_calls:
                try:
                    logger.info(f"Executed {len(function_calls)} function(s), sending results back to Gemini")
                    
                    # Prepare function responses in Gemini API format
                    gemini_function_responses = []
                    for func_result in function_results:
                        gemini_function_responses.append({
                            "name": func_result["function"],
                            "response": {"result": func_result["result"]}
                        })
                    
                    logger.info(f"Formatted function responses: {gemini_function_responses}")
                    
                    # Ensure conversation_history is a list (handle None case)
                    if conversation_history is None:
                        conversation_history = []
                    
                    # Per Gemini API docs, we need to append:
                    # 1. The user's original message
                    # 2. The model's response with function_call (even if message is empty)
                    # Then send the function response
                    updated_history = conversation_history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": ai_message or ""}  # Model's response with function call
                    ]
                    
                    # Send function results back to Gemini
                    logger.info("Calling Gemini with function results...")
                    final_response = await self.gemini_client.chat(
                        conversation_history=updated_history,
                        function_responses=gemini_function_responses,
                        system_instruction=SHOPPING_ASSISTANT_INSTRUCTION
                    )
                    
                    logger.info(f"Gemini final response: {final_response}")
                    
                    # Use the final response from Gemini
                    ai_message = final_response.get("message", "")
                    logger.info(f"Final AI message: '{ai_message}'")
                except Exception as e:
                    logger.error(f"Error getting final response from Gemini: {e}", exc_info=True)
                    ai_message = f"I found the product information, but encountered an error generating the response: {str(e)}"
            
            # Only return function_calls if we didn't complete the Function Calling flow
            # If we completed the flow, the final ai_message contains the complete response
            return_function_calls = [] if function_calls and ai_message else function_calls
            
            # Limit products to display (e.g., top 5)
            display_products = all_products[:5] if all_products else []
            
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
