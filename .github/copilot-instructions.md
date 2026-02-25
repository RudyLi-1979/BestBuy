# BestBuy Scanner - AI Coding Agent Instructions

## Architecture Overview

**Chat-First** Android app (Kotlin/MVVM) + Python FastAPI backend. `ChatActivity` is the LAUNCHER — the sole entry point.

```
ChatActivity ──POST /chat──→ UCP Server (localhost:58000)
   │                              │
   ├─ "📷 Scan" ──→ MainActivity  ├─ Gemini 2.5 Flash (function calling)
   │   (CameraX/ML Kit)           ├─ BestBuy API (product search / BOPIS)
   └─ Product Cards ←─────────────└─ cart_service / checkout_service / order_service
```

**Two distinct Retrofit clients** — never mix them:
- `RetrofitClient` + `BestBuyApiService` → `api.bestbuy.com` (direct Best Buy REST API)
- `UCPRetrofitClient` + `UCPApiService` → UCP Server (`POST /chat`, `GET /chat/session/{id}/history`, `DELETE /chat/session/{id}`)

## Critical Patterns

### UPC Cleaning (mandatory before every API call)
```kotlin
val cleanUpc = upc.trim().replace(" ", "")  // UPC-A(12), EAN-13(13), UPC-E(8) — numeric only
```

### BestBuy API URL format (non-standard path)
```
GET /v1/products(upc=190199246850)?apiKey=KEY&format=json   ✅
GET /v1/products?upc=190199246850                           ❌
```
Always add `@Query("show")` to limit fields and reduce payload size.

### API Key Access
```kotlin
private val apiKey = BuildConfig.BESTBUY_API_KEY  // loaded from .env at Gradle build time
```
Never hardcode keys. See [SECURITY.md](../SECURITY.md).

### Repository / Coroutines Pattern
```kotlin
// Repository: suspend + IO dispatcher + Result<T>
suspend fun search(upc: String): Result<Product> = withContext(Dispatchers.IO) { ... }

// ViewModel: launch on viewModelScope, expose LiveData (never MutableLiveData publicly)
viewModelScope.launch { _product.value = repo.search(upc).getOrNull() }
```

### Chat Personalization — `UserBehaviorContext`
Every `POST /chat` request includes `UserBehaviorContext` built from Room DB (`UserInteraction` table):
- `recentCategories`, `recentSkus`, `favoriteManufacturers`, `interactionCount`
- Minimum 5 tracked interactions before personalization kicks in

### Structured Logging
```kotlin
Log.d("Tag", "===========================================")
Log.d("Tag", "🔍 Searching UPC: $cleanUpc")
Log.d("Tag", "===========================================")
```

## Room Database — Current State

**Version 4** (`AppDatabase.kt`). All 4 migrations must remain in `.addMigrations(...)`.

| Version | Change |
|---------|--------|
| 1→2 | Added `user_interactions` table |
| 2→3 | Added `chat_messages` table (`ChatMessageEntity`) for local chat history |
| 3→4 | Added `regularPrice REAL`, `onSale INTEGER` to `cart_items` |

Chat history is loaded **from local Room DB** on resume — no server round-trip. Products in messages are serialized as JSON (`productsJson` column via Gson).

## UCP Server (Python FastAPI)

**Port**: `58000`. Key services: `bestbuy_client.py`, `gemini_client.py`, `chat_service.py`, `rate_limiter.py`.  
API routes: `chat.py`, `cart.py`, `checkout.py`, `orders.py`, `products.py`.

`bestbuy_client.py` `_filter_and_rank_results()`: scores exact spec matches (100pts) vs partial (50pts). Always pass full specs in Gemini queries:
- Wrong: `search_products(query="mac")` → Right: `search_products(query="mac mini 256GB")`

**Best Buy API coverage (~60%)**: ✅ UPC/SKU search, alsoViewed, alsoBought, store availability (BOPIS), advanced search. ❌ Open box, trending/most-viewed. See [BESTBUY_API_INTEGRATION_ANALYSIS.md](../BESTBUY_API_INTEGRATION_ANALYSIS.md).

## Development Workflow

### Android
```powershell
copy .env.example .env        # add BESTBUY_API_KEY
./gradlew clean build          # or Gradle sync in Android Studio
# Deploy to physical device — CameraX does not work on emulators
```
Test UPCs: `190199246850` (AirPods), `887276311111` (Samsung), `711719534464` (PlayStation).

### UCP Server
```powershell
cd ucp_server
.\start_docker.ps1             # Docker (recommended) → http://localhost:58000
# OR
.\venv\Scripts\activate ; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 58000
```

### Adding a Room Migration
1. Bump `version = N` in `AppDatabase.kt`
2. Add `MIGRATION_(N-1)_N` object with `execSQL`
3. Register in `.addMigrations(...)`

## Key Files

| File | Purpose |
|------|---------|
| [ChatActivity.kt](../app/src/main/java/com/bestbuy/scanner/ui/ChatActivity.kt) | Launcher; orchestrates chat, scan, cart badge |
| [UCPApiService.kt](../app/src/main/java/com/bestbuy/scanner/data/api/UCPApiService.kt) | Retrofit interface for UCP Server (`/chat`, `/session`) |
| [BestBuyApiService.kt](../app/src/main/java/com/bestbuy/scanner/data/api/BestBuyApiService.kt) | Retrofit interface for Best Buy API (UPC/SKU/search) |
| [AppDatabase.kt](../app/src/main/java/com/bestbuy/scanner/data/database/AppDatabase.kt) | Room DB v4; CartItem, UserInteraction, ChatMessageEntity |
| [ChatModels.kt](../app/src/main/java/com/bestbuy/scanner/data/model/ChatModels.kt) | ChatMessage, UserBehaviorContext, FunctionCall models |
| [ProductRepository.kt](../app/src/main/java/com/bestbuy/scanner/data/repository/ProductRepository.kt) | UPC cleaning reference + Result<T> pattern |
| [bestbuy_client.py](../ucp_server/app/services/bestbuy_client.py) | Best Buy API client with `_filter_and_rank_results()` |
| [chat_service.py](../ucp_server/app/services/chat_service.py) | Gemini function-call orchestration |
| [gemini_client.py](../ucp_server/app/services/gemini_client.py) | Gemini 2.5 Flash client |

## Agent Rules

1. Clean UPC before every API call
2. Use `BuildConfig.BESTBUY_API_KEY` — never hardcode keys
3. Repositories: `suspend` + `withContext(Dispatchers.IO)` + `Result<T>`
4. ViewModels: expose `LiveData` (not `MutableLiveData`) publicly
5. Room version changes always require a migration — never use `fallbackToDestructiveMigration`
6. Test camera features on physical devices only
7. Debug API 400s: check `.env` exists, UPC is all-numeric, review Logcat URL
