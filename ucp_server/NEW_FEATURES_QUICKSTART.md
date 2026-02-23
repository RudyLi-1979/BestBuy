# Testing New Features - Quick Start Guide

## Prerequisites
- Python virtual environment activated
- `.env` file with valid `BESTBUY_API_KEY`
- UCP Server dependencies installed

## Quick Test (1 minute)

### Verify Installation
```powershell
cd ucp_server

# Check imports
python -c "from app.services.bestbuy_client import BestBuyAPIClient; from app.schemas.store import Store; print('✅ All imports OK')"

# Check Gemini functions
python -c "from app.services.gemini_client import GeminiClient; print(f'Total functions: {len(GeminiClient().get_function_declarations())}')"
```

**Expected Output**:
```
✅ All imports OK
Total functions: 12
```

---

## Full Test Suite (5-10 minutes)

### Option 1: Automated Test Script (Recommended)
```powershell
cd ucp_server
.\test_new_features.ps1
```

This runs:
1. Direct API client tests (store availability, also-bought, advanced search)
2. Gemini chat integration tests

---

### Option 2: Manual Testing

#### Test 1: Store Availability
```powershell
python test_new_features.py
```

**What it tests**:
- Check iPhone 15 Pro availability near San Francisco (94103)
- Check MacBook Air M2 availability near NYC (10001)
- Display store details, distance, in-stock status

**Expected**: List of stores with inventory information

---

#### Test 2: Chat Integration
```powershell
python test_chat_new_features.py
```

**What it tests**:
- "Where can I buy iPhone 15 Pro near 94103?"
- "What do people buy with MacBook Air?"
- "Show me Apple laptops under $2000"

**Expected**: Natural language responses from Gemini AI

---

## Quick Feature Demos

### Demo 1: Store Availability (BOPIS)
```python
# Test directly in Python
python

>>> from app.services.bestbuy_client import BestBuyAPIClient
>>> import asyncio
>>> 
>>> client = BestBuyAPIClient()
>>> result = asyncio.run(client.get_store_availability(
...     sku="6428324",  # iPhone 15 Pro
...     postal_code="94103",
...     radius=25
... ))
>>> 
>>> print(f"Found {result.total_stores} stores")
>>> for store_avail in result.stores[:3]:
...     store = store_avail.store
...     print(f"{store.name} - {store.distance} miles - In Stock: {store_avail.in_stock}")
```

---

### Demo 2: Also Bought Recommendations
```python
>>> from app.services.bestbuy_client import BestBuyAPIClient
>>> import asyncio
>>> 
>>> client = BestBuyAPIClient()
>>> products = asyncio.run(client.get_also_bought("6428324"))  # iPhone 15 Pro
>>> 
>>> print(f"Also bought: {len(products)} products")
>>> for p in products[:5]:
...     print(f"- {p.name} (${p.sale_price or p.regular_price})")
```

---

### Demo 3: Advanced Search
```python
>>> from app.services.bestbuy_client import BestBuyAPIClient
>>> import asyncio
>>> 
>>> client = BestBuyAPIClient()
>>> result = asyncio.run(client.advanced_search(
...     query="laptop",
...     manufacturer="Apple",
...     max_price=2000.0,
...     free_shipping=True
... ))
>>> 
>>> print(f"Found {len(result.products)} products")
>>> for p in result.products[:3]:
...     print(f"- {p.name} (${p.sale_price or p.regular_price})")
```

---

## Troubleshooting

### Import Errors
```
❌ ModuleNotFoundError: No module named 'app.schemas.store'
```

**Solution**: Make sure you're in the `ucp_server` directory and virtual environment is activated
```powershell
cd ucp_server
.\venv\Scripts\Activate.ps1
```

---

### API Key Error
```
❌ Error: Missing BESTBUY_API_KEY
```

**Solution**: Create `.env` file in `ucp_server/` directory
```env
BESTBUY_API_KEY=your_api_key_here
GEMINI_API_KEY=your_gemini_key_here
```

---

### HTTP 403 Forbidden
```
❌ HTTPError: 403 Forbidden
```

**Solution**: Invalid API key. Verify your Best Buy API key at [developer.bestbuy.com](https://developer.bestbuy.com)

---

## Testing with Android App

### Step 1: Start UCP Server
```powershell
cd ucp_server
.\start_server.ps1
```

Server runs on: `http://localhost:8000`

### Step 2: Test Queries in Android App Chat Mode

**Store Availability**:
- "Where can I buy iPhone 15 Pro near 94103?"
- "Where can I buy a MacBook Air? I'm in New York 10001"
- "Check stores with iPad near me"

**Also Bought**:
- "What do people buy with AirPods Pro?"
- "What else do people buy with an iPhone 15 Pro?"
- "Show me items bought together with MacBook"

**Advanced Search**:
- "Show me Apple laptops under $2000"
- "I'm looking for a gaming laptop between $1500 and $2500"
- "Samsung phones with free shipping"
- "Find Sony headphones that are on sale"

---

## Success Criteria

✅ All imports work without errors  
✅ Gemini has 12 total functions (3 new ones)  
✅ `test_new_features.py` completes without errors  
✅ `test_chat_new_features.py` shows AI responses  
✅ Android app can query new features via chat  

---

## Next Steps

After successful testing:
1. ✅ Integration complete - features ready for production
2. 📱 Test in Android app chat mode with real devices
3. 📊 Monitor usage analytics for feature adoption
4. 🚀 Deploy to production server
5. 📝 Update user documentation with new capabilities

---

## Support

- Full documentation: [NEW_FEATURES_IMPLEMENTATION.md](../NEW_FEATURES_IMPLEMENTATION.md)
- API reference: [BESTBUY_API_INTEGRATION_ANALYSIS.md](../BESTBUY_API_INTEGRATION_ANALYSIS.md)
- Chat testing: [ucp_server/CHAT_TESTING.md](./CHAT_TESTING.md)

**Questions?** Check the documentation or review test scripts for examples.
