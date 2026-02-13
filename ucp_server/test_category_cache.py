"""
Test Category Cache Performance
Validates that commonly used categories are cached and reduce API calls
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.bestbuy_client import BestBuyAPIClient


async def test_category_cache():
    """Test that category cache reduces API calls"""
    client = BestBuyAPIClient()
    
    print("=" * 60)
    print("📦 CATEGORY CACHE TEST")
    print("=" * 60)
    
    try:
        # Get initial rate limiter stats
        initial_stats = client.rate_limiter.get_stats()
        initial_requests = initial_stats['requests_today']
        print(f"\n📊 Initial API requests today: {initial_requests}")
        
        # TEST 1: Search for common category (should use cache)
        print("\n🧪 TEST 1: First search for 'laptop' (COMMON_CATEGORIES cache)")
        print("-" * 60)
        result1 = await client.search_categories(name="laptop")
        print(f"✅ Found {result1.total} laptop categories")
        print(f"   Category ID: {result1.categories[0].id if result1.categories else 'N/A'}")
        
        stats1 = client.rate_limiter.get_stats()
        print(f"   API requests after test 1: {stats1['requests_today']}")
        print(f"   API calls made: {stats1['requests_today'] - initial_requests}")
        
        # Small delay
        await asyncio.sleep(0.5)
        
        # TEST 2: Search for same category again (should use cache)
        print("\n🧪 TEST 2: Second search for 'laptop' (should use cache)")
        print("-" * 60)
        result2 = await client.search_categories(name="laptop")
        print(f"✅ Found {result2.total} laptop categories (cached)")
        print(f"   Category ID: {result2.categories[0].id if result2.categories else 'N/A'}")
        
        stats2 = client.rate_limiter.get_stats()
        print(f"   API requests after test 2: {stats2['requests_today']}")
        print(f"   API calls made: {stats2['requests_today'] - stats1['requests_today']}")
        
        if stats2['requests_today'] == stats1['requests_today']:
            print("   🎯 CACHE HIT! No API call made")
        else:
            print("   ⚠️ Cache miss - API call made")
        
        # TEST 3: Search for 'desktops' (another common category)
        await asyncio.sleep(0.5)
        print("\n🧪 TEST 3: Search for 'desktop' (COMMON_CATEGORIES cache)")
        print("-" * 60)
        result3 = await client.search_categories(name="desktop")
        print(f"✅ Found {result3.total} desktop categories")
        print(f"   Category ID: {result3.categories[0].id if result3.categories else 'N/A'}")
        
        stats3 = client.rate_limiter.get_stats()
        print(f"   API requests after test 3: {stats3['requests_today']}")
        print(f"   API calls made: {stats3['requests_today'] - stats2['requests_today']}")
        
        # TEST 4: Search for 'phones' (another common category)
        await asyncio.sleep(0.5)
        print("\n🧪 TEST 4: Search for 'phones' (COMMON_CATEGORIES cache)")
        print("-" * 60)
        result4 = await client.search_categories(name="phones")
        print(f"✅ Found {result4.total} phone categories")
        print(f"   Category ID: {result4.categories[0].id if result4.categories else 'N/A'}")
        
        stats4 = client.rate_limiter.get_stats()
        print(f"   API requests after test 4: {stats4['requests_today']}")
        print(f"   API calls made: {stats4['requests_today'] - stats3['requests_today']}")
        
        # TEST 5: Search for uncommon category (should NOT use cache)
        await asyncio.sleep(0.5)
        print("\n🧪 TEST 5: Search for 'Camera*' (not in cache - will call API)")
        print("-" * 60)
        result5 = await client.search_categories(name="Camera*")
        print(f"✅ Found {result5.total} camera categories")
        if result5.categories:
            print(f"   First category: {result5.categories[0].name} ({result5.categories[0].id})")
        
        stats5 = client.rate_limiter.get_stats()
        print(f"   API requests after test 5: {stats5['requests_today']}")
        print(f"   API calls made: {stats5['requests_today'] - stats4['requests_today']}")
        
        if stats5['requests_today'] > stats4['requests_today']:
            print("   ✅ Expected - made API call for non-cached category")
        
        # TEST 6: Search for 'Camera*' again (should now be cached)
        await asyncio.sleep(0.5)
        print("\n🧪 TEST 6: Second search for 'Camera*' (should be cached now)")
        print("-" * 60)
        result6 = await client.search_categories(name="Camera*")
        print(f"✅ Found {result6.total} camera categories (should be cached)")
        
        stats6 = client.rate_limiter.get_stats()
        print(f"   API requests after test 6: {stats6['requests_today']}")
        print(f"   API calls made: {stats6['requests_today'] - stats5['requests_today']}")
        
        if stats6['requests_today'] == stats5['requests_today']:
            print("   🎯 CACHE HIT! Category was cached from previous search")
        
        # Summary
        print("\n" + "=" * 60)
        print("📈 SUMMARY")
        print("=" * 60)
        final_stats = client.rate_limiter.get_stats()
        total_api_calls = final_stats['requests_today'] - initial_requests
        print(f"Total API calls made in this test: {total_api_calls}")
        print(f"Expected without cache: 6 calls")
        print(f"Actual with cache: {total_api_calls} calls")
        print(f"API calls saved: {6 - total_api_calls}")
        print(f"Cache efficiency: {((6 - total_api_calls) / 6 * 100):.1f}%")
        
        print("\n✅ COMMON_CATEGORIES cached:")
        from app.services.bestbuy_client import COMMON_CATEGORIES
        for key, value in COMMON_CATEGORIES.items():
            print(f"   - {key}: {value}")
        
        print(f"\n✅ Runtime cache size: {len(client._category_cache)} categories")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()
        print("\n🔒 Client closed")


if __name__ == "__main__":
    asyncio.run(test_category_cache())
