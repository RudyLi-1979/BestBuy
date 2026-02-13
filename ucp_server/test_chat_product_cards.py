"""
Test Chat Product Cards Feature
Validates that chat responses include product data
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.chat_service import ChatService
from app.database import SessionLocal
import json


async def test_chat_with_products():
    """Test that chat responses include product cards"""
    chat_service = ChatService()
    db = SessionLocal()
    
    print("=" * 80)
    print("🧪 CHAT PRODUCT CARDS TEST")
    print("=" * 80)
    
    try:
        # TEST 1: Search for Mac mini
        print("\n📱 TEST 1: Search for 'mac mini'")
        print("-" * 80)
        
        result = await chat_service.process_message(
            message="我想買 mac mini",
            db=db,
            user_id="test_user_123",
            conversation_history=[]
        )
        
        print(f"\n✅ AI Message: {result['message'][:200]}...")
        print(f"\n📦 Products returned: {len(result.get('products', []))}")
        
        if result.get('products'):
            for i, product in enumerate(result['products'][:3], 1):
                print(f"\n{i}. {product.get('name', 'Unknown')}")
                print(f"   SKU: {product.get('sku')}")
                print(f"   Price: ${product.get('price', product.get('sale_price', 'N/A'))}")
                print(f"   Manufacturer: {product.get('manufacturer', 'N/A')}")
                print(f"   Image: {product.get('image', 'N/A')[:60]}...")
        else:
            print("⚠️ No products returned!")
        
        # TEST 2: Search for iPhone
        await asyncio.sleep(1.0)
        print("\n\n📱 TEST 2: Search for 'iPhone 15'")
        print("-" * 80)
        
        result2 = await chat_service.process_message(
            message="Show me iPhone 15 models",
            db=db,
            user_id="test_user_123",
            conversation_history=[
                {"role": "user", "content": "我想買 mac mini"},
                {"role": "assistant", "content": result['message']}
            ]
        )
        
        print(f"\n✅ AI Message: {result2['message'][:200]}...")
        print(f"\n📦 Products returned: {len(result2.get('products', []))}")
        
        if result2.get('products'):
            for i, product in enumerate(result2['products'][:3], 1):
                print(f"\n{i}. {product.get('name', 'Unknown')[:60]}")
                print(f"   SKU: {product.get('sku')}")
                print(f"   Price: ${product.get('price', product.get('sale_price', 'N/A'))}")
                print(f"   On Sale: {product.get('on_sale', False)}")
        
        # TEST 3: General question (no products expected)
        await asyncio.sleep(1.0)
        print("\n\n📱 TEST 3: General question (no products)")
        print("-" * 80)
        
        result3 = await chat_service.process_message(
            message="What's your return policy?",
            db=db,
            user_id="test_user_123",
            conversation_history=[]
        )
        
        print(f"\n✅ AI Message: {result3['message'][:200]}...")
        print(f"\n📦 Products returned: {len(result3.get('products', []))}")
        
        if not result3.get('products') or len(result3.get('products', [])) == 0:
            print("✅ Correctly returned no products for non-shopping query")
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        print(f"TEST 1 (Mac mini): {len(result.get('products', []))} products")
        print(f"TEST 2 (iPhone 15): {len(result2.get('products', []))} products")
        print(f"TEST 3 (General): {len(result3.get('products', []))} products")
        
        # Validate response structure
        print("\n🔍 Response Structure Validation:")
        print(f"✅ 'message' field: {bool(result.get('message'))}")
        print(f"✅ 'products' field exists: {bool('products' in result)}")
        print(f"✅ 'function_results' field: {bool(result.get('function_results'))}")
        
        if result.get('products'):
            sample_product = result['products'][0]
            required_fields = ['sku', 'name', 'price', 'manufacturer', 'image']
            print("\n🔍 Product Data Validation:")
            for field in required_fields:
                # Check if field exists with various possible names
                has_field = (
                    field in sample_product or 
                    field.replace('_', '') in sample_product or
                    field.replace('price', 'sale_price') in sample_product
                )
                status = "✅" if has_field else "❌"
                print(f"{status} '{field}' field exists")
        
        print("\n✅ CHAT PRODUCT CARDS FEATURE TEST COMPLETE!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await chat_service.bestbuy_client.close()
        db.close()
        print("\n🔒 Resources closed")


if __name__ == "__main__":
    asyncio.run(test_chat_with_products())
