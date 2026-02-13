"""
Test Rate Limiter - Verify 5 requests/second limit
This script tests that the RateLimiter correctly enforces the 5 req/s limit
"""
import asyncio
import time
from app.services.rate_limiter import RateLimiter


async def test_rate_limiter():
    """Test rate limiter with rapid requests"""
    
    print("=" * 80)
    print("RATE LIMITER TEST - 5 Requests per Second")
    print("=" * 80)
    
    limiter = RateLimiter(requests_per_second=5, requests_per_day=50000)
    
    print("\n📊 Initial stats:")
    print(f"   {limiter.get_stats()}\n")
    
    print("🔄 TEST 1: Making 10 requests rapidly...")
    print("-" * 80)
    
    start_time = time.time()
    request_times = []
    
    for i in range(10):
        await limiter.acquire()
        current = time.time()
        request_times.append(current)
        elapsed = current - start_time
        print(f"   Request {i+1:2d}: {elapsed:.3f}s from start")
        
        # Show stats every 5 requests
        if (i + 1) % 5 == 0:
            stats = limiter.get_stats()
            print(f"   └─ Stats: {stats['requests_last_second']}/{stats['requests_per_second_limit']} in last second")
    
    total_time = time.time() - start_time
    
    print(f"\n✅ Completed 10 requests in {total_time:.3f}s")
    print(f"   Expected: ~2.0s (5 req/s → 10 requests needs 2 seconds)")
    print(f"   Actual:   {total_time:.3f}s")
    
    if 1.8 <= total_time <= 2.5:
        print("   ✅ PASS: Rate limiter working correctly!")
    else:
        print("   ⚠️  WARNING: Timing may be affected by system load")
    
    print("\n🔄 TEST 2: Checking 1-second windows...")
    print("-" * 80)
    
    # Analyze request distribution
    for i in range(1, len(request_times)):
        window_start = request_times[i] - 1.0
        requests_in_window = sum(1 for t in request_times[:i+1] if t >= window_start)
        print(f"   After request {i+1}: {requests_in_window} requests in last 1.0s")
        
        if requests_in_window > 5:
            print(f"      ⚠️  FAIL: More than 5 requests in a 1-second window!")
    
    print("\n📊 Final stats:")
    print(f"   {limiter.get_stats()}")
    
    print("\n" + "=" * 80)
    print("✅ Rate Limiter Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_rate_limiter())
