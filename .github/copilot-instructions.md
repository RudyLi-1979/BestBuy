# BestBuy Scanner - AI Coding Agent Instructions

## Project Overview

Android barcode scanner app using **MVVM architecture** with CameraX, ML Kit, and BestBuy API integration. Written in **Kotlin** with manual dependency injection (no Hilt/Koin). Includes shopping cart persistence via Room Database, personalized recommendations engine, and Python FastAPI backend for Gemini integration.

## Critical Patterns

### API Key Management
- **NEVER hardcode API keys** - always use `BuildConfig.BESTBUY_API_KEY`
- API key is loaded from `.env` file at build time via `app/build.gradle.kts`
- Example: `private val apiKey = BuildConfig.BESTBUY_API_KEY`
- See [SECURITY.md](../SECURITY.md) for complete guidelines

### UPC Barcode Processing
Always clean UPC input before API calls:
```kotlin
val cleanUpc = upc.trim().replace(" ", "")
```
Valid formats: UPC-A (12), EAN-13 (13), UPC-E (8) - all numeric. See [ProductRepository.kt](../app/src/main/java/com/bestbuy/scanner/data/repository/ProductRepository.kt#L27-L29) for reference implementation.

### API Request Patterns
- BestBuy API uses unique path format: `products(upc={upc})` not `products?upc={upc}`
- Always include `@Query("format") format: String = "json"`
- Use `@Query("show")` parameter to specify exact fields (reduces response size)
- See [BestBuyApiService.kt](../app/src/main/java/com/bestbuy/scanner/data/api/BestBuyApiService.kt) for all endpoint signatures

### Logging Standards
Use structured logging with visual separators for debugging:
```kotlin
android.util.Log.d("ComponentName", "===========================================")
android.util.Log.d("ComponentName", "🔍 Operation description")
android.util.Log.d("ComponentName", "Key data: $value")
android.util.Log.d("ComponentName", "===========================================")
```
See [ProductRepository.kt](../app/src/main/java/com/bestbuy/scanner/data/repository/ProductRepository.kt#L28-L36) for examples.

### Coroutines & LiveData
- All repository methods use `suspend fun` with `withContext(Dispatchers.IO)`
- ViewModel launches coroutines with `viewModelScope.launch`
- Return `Result<T>` from repository methods for cleaner error handling
- Use `MutableLiveData` privately, expose as `LiveData` publicly in ViewModels

## Architecture Layers

```
View (MainActivity.kt, ProductDetailActivity.kt, CartActivity.kt)
  ↓ observes LiveData
ViewModel (ProductViewModel, CartViewModel, RecommendationViewModel)
  ↓ calls repository
Repository (ProductRepository, CartRepository, RecommendationRepository)
  ↓ ├─ API: BestBuyApiService (Retrofit)
    ├─ DB: Room Database (CartDao, UserInteractionDao)
    └─ Logic: RecommendationEngine
```

**Manual DI**: Components instantiated directly in ViewModels (e.g., `private val repository = ProductRepository()`)

## Key Features & Components

### Shopping Cart
- **Local storage**: Room Database (AppDatabase.kt, v2)
- **DAOs**: CartDao.kt, UserInteractionDao.kt
- **Models**: CartItem.kt, UserInteraction.kt
- **ViewModel**: CartViewModel.kt manages add/remove/clear operations
- **Adapter**: CartAdapter.kt for RecyclerView display
- **Persistence**: All cart operations saved to Room DB

### Personalized Recommendations
- **Engine**: RecommendationEngine.kt analyzes user viewing/scanning behavior
- **Tracking**: UserBehaviorRepository.kt tracks interactions (views, scans, cart adds)
- **Algorithm**: Filters by category preference, excludes viewed items, requires min 5 interactions
- **Backend**: Python UCP server (`/ucp_server/`) for Gemini API integration
- **Adapter**: PersonalizedRecommendationAdapter.kt for UI display

### Chat Mode & Search Optimization (UCP Server)
- **Backend**: Python FastAPI server in `/ucp_server/` with Gemini 2.5 Flash integration
- **Intelligent Search**: `bestbuy_client.py` includes `_filter_and_rank_results()` method:
  - Extracts specifications from queries (storage: "256GB", colors, models)
  - Scores products by relevance (exact matches score 100, spec matches score 50)
  - Filters out products missing user-specified specs
  - Changed default sort from `bestSellingRank.asc` to `name.asc` for consistency
- **Gemini Instructions**: System prompt guides AI to include ALL specifications in search queries
  - Wrong: `search_products(query="mac")` → Right: `search_products(query="mac mini 256GB")`
- **API Integration Status**: ~60% of Best Buy API implemented
  - ✅ Implemented: 
    - Search by UPC/SKU, product search
    - alsoViewed & alsoBought recommendations
    - Store availability query (BOPIS - Buy Online, Pick-up In Store)
    - Advanced search operators (price range, manufacturer, category, shipping filters)
  - ❌ Missing: Categories API, open box products, trending/most viewed, advanced operators (AND/OR/IN)
  - See [BESTBUY_API_INTEGRATION_ANALYSIS.md](../BESTBUY_API_INTEGRATION_ANALYSIS.md) for complete analysis
- **New Features (2026-02-13)**:
  - **Store Availability** (`get_store_availability`): Check product inventory at nearby physical stores for in-store pickup, O2O value
  - **Also Bought** (`get_also_bought`): Cross-sell recommendations - products frequently bought together, increases average order value
  - **Advanced Search** (`advanced_search`): Multi-criteria filtering (manufacturer, price range, category, shipping options, sale status)
- **Setup**: See [ucp_server/README.md](../ucp_server/README.md) for Python environment

### Barcode Scanning
- **CameraX** with Preview, ImageAnalysis for real-time camera processing
- **ML Kit** for barcode detection and parsing
- **Analyzer**: BarcodeScannerAnalyzer.kt processes camera frames
- **Format Support**: UPC-A (12 digits), EAN-13 (13 digits), UPC-E (8 digits)

## Key Files

| File | Purpose |
|------|---------|
| [BestBuyApiService.kt](../app/src/main/java/com/bestbuy/scanner/data/api/BestBuyApiService.kt) | Retrofit API endpoint definitions (searchByUPC, getBySKU, searchProducts) |
| [RetrofitClient.kt](../app/src/main/java/com/bestbuy/scanner/data/api/RetrofitClient.kt) | Retrofit config with 30s timeout, logging interceptor |
| [ProductRepository.kt](../app/src/main/java/com/bestbuy/scanner/data/repository/ProductRepository.kt) | Data access layer with UPC cleaning, Result<T> error handling |
| [ProductViewModel.kt](../app/src/main/java/com/bestbuy/scanner/ui/viewmodel/ProductViewModel.kt) | Product search, recommendations, state management via LiveData |
| [CartRepository.kt](../app/src/main/java/com/bestbuy/scanner/data/repository/CartRepository.kt) | Shopping cart CRUD operations with Room |
| [CartViewModel.kt](../app/src/main/java/com/bestbuy/scanner/ui/viewmodel/CartViewModel.kt) | Cart state management, total price calculation |
| [RecommendationRepository.kt](../app/src/main/java/com/bestbuy/scanner/data/repository/RecommendationRepository.kt) | Gets also-viewed and recommendations from API |
| [RecommendationEngine.kt](../app/src/main/java/com/bestbuy/scanner/data/recommendation/RecommendationEngine.kt) | Personalized recommendation algorithm |
| [AppDatabase.kt](../app/src/main/java/com/bestbuy/scanner/data/database/AppDatabase.kt) | Room database schema v2 with entities |
| [MainActivity.kt](../app/src/main/java/com/bestbuy/scanner/ui/MainActivity.kt) | Barcode scanning UI with CameraX setup |
| [ProductDetailActivity.kt](../app/src/main/java/com/bestbuy/scanner/ui/ProductDetailActivity.kt) | Product details, recommendations, cart integration |
| [CartActivity.kt](../app/src/main/java/com/bestbuy/scanner/ui/CartActivity.kt) | Shopping cart display and management |
| [BarcodeScannerAnalyzer.kt](../app/src/main/java/com/bestbuy/scanner/utils/BarcodeScannerAnalyzer.kt) | CameraX ImageAnalysis for ML Kit barcode detection |
| [bestbuy_client.py](../ucp_server/app/services/bestbuy_client.py) | UCP Server Best Buy API client with intelligent search filtering |
| [gemini_client.py](../ucp_server/app/services/gemini_client.py) | Gemini 2.5 Flash client with function calling support |
| [chat_service.py](../ucp_server/app/services/chat_service.py) | Chat orchestration - executes Gemini function calls |
| [store.py](../ucp_server/app/schemas/store.py) | Store and StoreAvailability schemas for BOPIS feature |

## Common Issues & Debugging

### API Error 400 (Bad Request)
1. Verify `.env` file exists with valid `BESTBUY_API_KEY`
2. Check UPC format (must be all numeric, 8-14 digits)
3. Review logged API URL format in Logcat
4. See [TROUBLESHOOTING_API_400.md](../TROUBLESHOOTING_API_400.md) for complete diagnosis

### Build Issues
```powershell
# Clean and rebuild
./gradlew clean build

# Sync after .env changes
# Then: Gradle sync in Android Studio
```

### Camera Testing
- **Use physical device** - emulators don't support CameraX well
- Test UPCs: `190199246850` (AirPods), `887276311111` (Samsung), `711719534464` (PlayStation)
- See [API_TESTING.md](../API_TESTING.md) for more test data

## Development Workflow

1. **Setup**: Copy `.env.example` → `.env`, add API key
2. **Build**: `./gradlew build` or Android Studio sync
3. **Run**: Deploy to physical device (camera required)
4. **Test**: Scan barcodes or use test UPCs from [QUICKSTART.md](../QUICKSTART.md)

## Code Style

- **Package structure**: `com.bestbuy.scanner.{data|ui|utils}`
- **Naming**: Activities end with `Activity`, ViewModels with `ViewModel`, Adapters with `Adapter`
- **Comments**: Use KDoc for public methods, Chinese comments where needed for clarity
- **View Binding**: Enabled globally, use `binding.viewId` pattern

## Package Organization

```
src/main/java/com/bestbuy/scanner/
├── data/
│   ├── api/              # BestBuyApiService, RetrofitClient
│   ├── database/         # AppDatabase, Room setup
│   ├── dao/              # CartDao, UserInteractionDao (DAOs)
│   ├── model/            # Product, CartItem, UserInteraction (data models)
│   ├── recommendation/   # RecommendationEngine
│   └── repository/       # ProductRepository, CartRepository, etc.
├── ui/
│   ├── viewmodel/        # ProductViewModel, CartViewModel, etc.
│   ├── adapter/          # CartAdapter, RecommendationAdapter, etc.
│   ├── MainActivity.kt
│   ├── ProductDetailActivity.kt
│   └── CartActivity.kt
└── utils/
    ├── BarcodeScannerAnalyzer.kt
    └── ApiDebugHelper.kt (debug utilities)
```

## Dependencies

Key libraries (see [app/build.gradle.kts](../app/build.gradle.kts)):
- CameraX 1.3.1 - Camera operations
- ML Kit 17.2.0 - Barcode scanning
- Retrofit 2.9.0 + OkHttp 4.12.0 - Networking
- Coroutines 1.7.3 - Async operations
- Lifecycle 2.7.0 - ViewModel/LiveData
- Room Database - Local persistence
- Glide 4.16.0 - Image loading

## Important Rules for Agents

1. **Always clean UPC codes** before API calls (trim + remove spaces)
2. **Never log sensitive data** (API keys, personal info)
3. **Use Result<T> pattern** in repository methods for consistent error handling
4. **Dispatch to IO** for all network/database operations
5. **Test on physical devices** - emulator camera support is limited
6. **Check .env file** first when API calls fail with 400 errors
7. **ViewModels manage UI state** - keep repositories pure data layers
8. **Use LiveData for observation** - never expose MutableLiveData publicly

## Documentation References

- [ARCHITECTURE.md](../ARCHITECTURE.md) - Detailed architecture diagrams and data flows
- [QUICKSTART.md](../QUICKSTART.md) - Setup steps and test UPCs
- [SECURITY.md](../SECURITY.md) - API key management best practices
- [API_TESTING.md](../API_TESTING.md) - curl commands for API testing
- [README.md](../README.md) - Feature overview and project structure
