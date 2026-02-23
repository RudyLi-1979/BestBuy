# API Rate Limiting Guide

## Best Buy API Limits

| Limit Type | Value | Description |
|---|---|---|
| **Requests per second** | 5 requests/second | Short-term limit |
| **Requests per day** | 50,000 requests/day | Long-term limit |

## RateLimiter Implementation

The UCP Server automatically applies rate limiting to all Best Buy API calls:

```python
class BestBuyAPIClient:
    def __init__(self):
        # Automatically initialize RateLimiter (5 req/s, 50k req/day)
        self.rate_limiter = RateLimiter(
            requests_per_second=5,
            requests_per_day=50000
        )
    
    async def search_products(self, query):
        # Automatically wait for the rate limiter at the start of each API method
        await self.rate_limiter.acquire()
        # ... make the API call
```

### How It Works

1. **Token Bucket Algorithm**: Uses a sliding window to track requests in the last second.
2. **Automatic Waiting**: If the limit is reached, it automatically sleeps until the next request can be made.
3. **Daily Tracking**: Tracks the total number of requests within a 24-hour period.

## Notes for Testing

### ✅ Good Practices

```python
# 1. RateLimiter handles it automatically (no manual waiting needed)
client = BestBuyAPIClient()
result1 = await client.search_products("iPhone")  # RateLimiter is applied automatically
result2 = await client.search_products("MacBook") # RateLimiter is applied automatically

# 2. Add extra delay between tests (recommended)
await asyncio.sleep(0.3)  # Between different types of tests

# 3. Reduce page_size in tests
result = await client.search_products("laptop", page_size=2)  # instead of 10
```

### ❌ To Avoid

```python
# ❌ Do not bypass the RateLimiter
# Wrong: Using httpx directly instead of BestBuyAPIClient
async with httpx.AsyncClient() as client:
    response = await client.get("https://api.bestbuy.com/...")

# ❌ Do not call rapidly multiple times in a loop
for i in range(10):
    await client.search_products(f"product{i}")  # The RateLimiter will handle it, but the test will slow down

# ❌ Do not use an overly large page_size
result = await client.search_products("laptop", page_size=100)  # Wastes quota
```

## Rate Limiting in Test Scripts

All test scripts have been updated to respect rate limits:

### 1. `test_rate_limiter.py`
**Purpose**: Verify that the RateLimiter correctly enforces the 5 req/s limit

```bash
python test_rate_limiter.py
```

**Expected Output**:
- 10 requests should complete in ~2.0 seconds
- A maximum of 5 requests within any 1-second window

### 2. `test_categories.py`
**Update**: Added a 0.3-second delay between each test

```bash
python test_categories.py
```

**API calls**: 5 times
- 4 times `search_categories`
- 1 time `advanced_search`

**Estimated time**: ~2 seconds (with delay)

### 3. `test_categories_simple.py`
**Update**: Added 0.3-second delay between API calls

```bash
python test_categories_simple.py
```

**API calls**: 2 times
**Estimated time**: ~0.5 seconds

### 4. `test_gemini_categories.py`
**Update**: 1.0-second interval between queries

```bash
python test_gemini_categories.py
```

**API calls**: Depends on Gemini function calls (usually 3-6 times)
**Estimated time**: ~3-5 seconds

## Monitoring API Usage

### Check RateLimiter Statistics

```python
client = BestBuyAPIClient()
stats = client.rate_limiter.get_stats()

print(stats)
# {
#     'requests_last_second': 3,
#     'requests_per_second_limit': 5,
#     'requests_today': 127,
#     'requests_per_day_limit': 50000,
#     'daily_reset_in_seconds': 82341.2
# }
```

### Log Output

RateLimiter automatically logs:

```
INFO     Rate limiter initialized: 5 req/s, 50000 req/day
DEBUG    Request allowed. Recent: 3/5, Daily: 127/50000
DEBUG    Rate limit: 5/5 requests in last second. Waiting 0.234s
WARNING  Daily limit reached (50000 requests). Waiting 1234.5s until reset
```

## Error Handling

### HTTP 403 Over Quota

If you see this error:

```
HTTP error: Client error '403 Over Quota'
```

**Cause**: Exceeded daily 50,000 request limit

**Solution**:
1. Wait for daily reset (UTC midnight)
2. Check if other services are using the same API key
3. Consider reducing test frequency or optimizing API calls

### HTTP 429 Too Many Requests

If you see this error:

```
HTTP error: Client error '429 Too Many Requests'
```

**Cause**: Exceeded 5 requests per second limit (RateLimiter failed or bypassed)

**Solution**:
1. Ensure using `BestBuyAPIClient` instead of direct API calls
2. Check if multiple client instances are running simultaneously
3. Increase delay between tests

## Optimizing API Usage

### 1. Use On-Demand Loading

```python
# ❌ Old way: Get store info every search (5+ API calls)
products = await client.search_products("iPhone")
for product in products:
    stores = await client.get_store_availability(product.sku, "94103")

# ✅ New way: Only get store info when user asks
products = await client.search_products("iPhone", page_size=2)
# Only when user explicitly requests:
stores = await client.get_store_availability(selected_sku, zip_code)
```

### 2. Reduce Default Result Count

```python
# ❌ Old setting: Default 10 results
DEFAULT_PAGE_SIZE = 10  # 1 search = 1 API call

# ✅ New setting: Default 2 results
DEFAULT_PAGE_SIZE = 2   # Save API quota, faster response
```

### 3. Use Wildcards Correctly

```python
# ✅ Correct: Only use trailing wildcard
result = await client.search_categories(name="Laptop*")
result = await client.search_categories(name="Phone*")

# ❌ Wrong: Best Buy API doesn't support leading or both-sided wildcards (returns 400)
result = await client.search_categories(name="*Phone*")
result = await client.search_categories(name="*Laptop")
```

### 4. Cache Common Data

```python
# Consider caching categories list (doesn't change often)
if not hasattr(self, '_categories_cache'):
    self._categories_cache = await client.get_categories()
```

## Development Vs Production Environments

### Development Environment
- Use smaller `page_size` (2-5)
- Add delays between tests
- Regularly check API usage statistics

### Production Environment
- RateLimiter automatically handles all requests
- Monitor daily usage alerts (e.g. 40k/50k)
- Implement caching strategy to reduce duplicate requests

## Testing Checklist

Before running tests:

- [ ] Confirm valid `BESTBUY_API_KEY` in `.env`
- [ ] Check if API quota remains today (< 50,000 requests)
- [ ] Tests use small `page_size` parameter
- [ ] Don't run multiple test scripts simultaneously
- [ ] Watch logs to confirm RateLimiter is working

---

**Updated**: 2026-02-13  
**Maintained by**: UCP Server Team
