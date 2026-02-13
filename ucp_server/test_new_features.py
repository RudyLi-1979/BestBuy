"""
Test script for new Best Buy API features
Tests: Store Availability, Also Bought, Advanced Search
"""
import asyncio
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.bestbuy_client import BestBuyAPIClient
from app.config import settings
import json


async def test_store_availability():
    """Test store availability query (BOPIS)"""
    print("\n" + "="*80)
    print("TEST 1: Store Availability Query (門市庫存查詢)")
    print("="*80)
    
    client = BestBuyAPIClient()
    
    # Test products - REDUCED to avoid API quota (403 errors)
    # Each store check requires 1 API call per store + 1 for product info
    # NOTE: SKU 6428324 is Xbox Series X, not iPhone (Best Buy SKU changed)
    test_cases = [
        {"sku": "6565875", "name": "MacBook Pro 14-inch M5", "zip": "94103"},  # San Francisco (use valid SKU from search results)
        # Reduced to 1 test case to avoid quota issues
    ]
    
    for case in test_cases:
        print(f"\n🏪 Testing: {case['name']} (SKU: {case['sku']}) near {case['zip']}")
        
        result = await client.get_store_availability(
            sku=case['sku'],
            postal_code=case['zip'],
            radius=25,
            max_stores=3  # Reduced from 5 to minimize API calls
        )
        
        print(f"Product: {result.product_name}")
        print(f"Stores found: {result.total_stores}")
        
        for i, store_avail in enumerate(result.stores[:3], 1):
            store = store_avail.store
            print(f"\n  Store {i}: {store.name}")
            print(f"    Address: {store.address}, {store.city}, {store.region}")
            print(f"    Distance: {store.distance} miles")
            print(f"    In Stock: {'✅' if store_avail.in_stock else '❌'}")
            print(f"    Pickup Available: {'✅' if store_avail.pickup_available else '❌'}")
            print(f"    Phone: {store.phone}")
    
    await client.close()
    print("\n✅ Store availability test completed\n")


async def test_also_bought():
    """Test also-bought recommendations"""
    print("\n" + "="*80)
    print("TEST 2: Also Bought Recommendations (alsoBought 推薦)")
    print("="*80)
    
    client = BestBuyAPIClient()
    
    # Test products - REDUCED to avoid API quota
    # NOTE: SKU 6428324 is Xbox Series X, using MacBook Pro instead
    test_cases = [
        {"sku": "6565875", "name": "MacBook Pro 14-inch M5"},  # Valid SKU from search results
        # Reduced to 1 test case to conserve API quota
    ]
    
    for case in test_cases:
        print(f"\n🛒 Testing: {case['name']} (SKU: {case['sku']})")
        
        also_bought = await client.get_also_bought(case['sku'])
        
        print(f"Found {len(also_bought)} also-bought products:")
        
        for i, product in enumerate(also_bought[:3], 1):  # Show only 3 to reduce output
            price = product.sale_price or product.regular_price
            print(f"  {i}. {product.name}")
            print(f"     Price: ${price:.2f} | SKU: {product.sku}")
            if product.on_sale:
                print(f"     💰 On Sale! (Was: ${product.regular_price:.2f})")
    
    await client.close()
    print("\n✅ Also-bought test completed\n")


async def test_advanced_search():
    """Test advanced search with filters"""
    print("\n" + "="*80)
    print("TEST 3: Advanced Search (進階搜尋操作符)")
    print("="*80)
    
    client = BestBuyAPIClient()
    
    # Test cases with various filters - REDUCED to avoid API quota
    test_cases = [
        {
            "name": "Apple laptops under $2000",
            "query": "laptop",
            "manufacturer": "Apple",
            "max_price": 2000.0
        },
        {
            "name": "Samsung Galaxy phones",
            "query": "Galaxy",  # More specific keyword
            "manufacturer": "Samsung"
            # Removed free_shipping filter to get more results
        }
        # Reduced to 2 test cases to conserve API quota
    ]
    
    for case in test_cases:
        print(f"\n🔍 Testing: {case['name']}")
        print(f"   Filters: {json.dumps({k: v for k, v in case.items() if k != 'name'}, indent=2)}")
        
        result = await client.advanced_search(
            query=case.get("query"),
            manufacturer=case.get("manufacturer"),
            category=case.get("category"),
            min_price=case.get("min_price"),
            max_price=case.get("max_price"),
            on_sale=case.get("on_sale"),
            free_shipping=case.get("free_shipping"),
            in_store_pickup=case.get("in_store_pickup"),
            page_size=5
        )
        
        print(f"\n   Found {result.total} products (showing top 5):")
        
        for i, product in enumerate(result.products[:5], 1):
            price = product.sale_price or product.regular_price
            print(f"\n   {i}. {product.name}")
            print(f"      Manufacturer: {product.manufacturer}")
            print(f"      Price: ${price:.2f}", end="")
            if product.on_sale:
                print(f" (SALE - was ${product.regular_price:.2f})", end="")
            print()
            print(f"      SKU: {product.sku}")
            if product.free_shipping:
                print(f"      🚚 Free Shipping")
            if product.in_store_availability:
                print(f"      🏪 In-Store Pickup Available")
    
    await client.close()
    print("\n✅ Advanced search test completed\n")


async def test_all():
    """Run all tests"""
    print("\n" + "="*80)
    print("🧪 TESTING NEW BEST BUY API FEATURES")
    print("="*80)
    print(f"API Key configured: {'✅ Yes' if settings.bestbuy_api_key else '❌ No'}")
    print(f"Base URL: {settings.bestbuy_api_base_url}")
    
    try:
        # Test 1: Store Availability
        await test_store_availability()
        
        # Test 2: Also Bought
        await test_also_bought()
        
        # Test 3: Advanced Search
        await test_advanced_search()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_all())
