# Project Architecture Description

## Overall Architecture

This project adopts a **Chat-First Architecture**, consisting of two main parts: the Android App and the UCP Server:

```
┌─────────────────────────────────────────────────────┐
│                   Android App                        │
│                 (Kotlin + MVVM)                     │
│                                                      │
│  ChatActivity (Main screen) ──┐                     │
│      ↓                    │                          │
│  ChatViewModel            │                          │
│      ↓                    │                          │
│  ChatRepository ──────────┼──→ UCP Server           │
│                           │                          │
│  MainActivity (Scanning) ─────┘                      │
│  ProductDetailActivity                              │
│  CartActivity                                       │
└──────────────────┬──────────────────────────────────┘
                   │ HTTPS (Cloudflare Tunnel)
                   │
┌──────────────────▼──────────────────────────────────┐
│                 UCP Server                           │
│             (Python + FastAPI)                      │
│                                                      │
│  Routes: /chat  /products  /cart  /checkout  /orders│
│      ↓                                              │
│  ChatService                                        │
│      ↓                                              │
│  ┌──────────────┐  ┌────────────────────────────┐  │
│  │ Gemini 2.5   │  │ BestBuyAPIClient           │  │
│  │ Flash Client │  │ - search_products()        │  │
│  │              │  │ - get_store_availability() │  │
│  │ Function     │  │ - get_also_bought()        │  │
│  │ Calling      │  │ - advanced_search()        │  │
│  └──────────────┘  │ - get_categories()         │  │
│                    │ - get_complementary_products│ │
│                    └────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## Android App MVVM Architecture

This project follows the MVVM (Model-View-ViewModel) architecture pattern:

```
┌─────────────────────────────────────────────────────┐
│                      View Layer                      │
│  (Activity, Fragment, XML Layouts)                  │
│                                                      │
│  - ChatActivity.kt (Main screen)                    │
│  - MainActivity.kt (Scanning)                       │
│  - ProductDetailActivity.kt                         │
│  - CartActivity.kt                                  │                         │
│  - activity_main.xml                                │
│  - activity_product_detail.xml                      │
└──────────────────┬──────────────────────────────────┘
                   │
                   │ observes LiveData
                   │
┌──────────────────▼──────────────────────────────────┐
│                   ViewModel Layer                    │
│  (Business Logic, State Management)                 │
│                                                      │
│  - ProductViewModel.kt                              │
│    • searchProductByUPC()                           │
│    • getProductBySKU()                              │
│    • loadRecommendations()                          │
└──────────────────┬──────────────────────────────────┘
                   │
                   │ calls repository
                   │
┌──────────────────▼──────────────────────────────────┐
│                 Repository Layer                     │
│  (Data Access, Business Logic)                      │
│                                                      │
│  - ProductRepository.kt                             │
│    • searchProductByUPC()                           │
│    • getRecommendations()                           │
└──────────────────┬──────────────────────────────────┘
                   │
                   │ uses API service
                   │
┌──────────────────▼──────────────────────────────────┐
│                   Data Layer                         │
│  (API, Models, Data Sources)                        │
│                                                      │
│  - BestBuyApiService.kt                             │
│  - RetrofitClient.kt                                │
│  - Product.kt (Data Models)                         │
└─────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Chat Mode Conversation Flow (New)

```
User types message in ChatActivity
       ↓
ChatViewModel.sendMessage()
       ↓
ChatRepository.sendMessage()
       ↓
UCP Server /chat API (Cloudflare Tunnel)
       ↓
ChatService.process_message()
       ↓
GeminiClient.generate_content()
       ↓
Gemini 2.5 Flash AI analyzes intent
       ↓
If function call needed:
  ChatService.execute_function()
       ↓
  BestBuyAPIClient (search/availability/etc)
       ↓
  Return results to Gemini
       ↓
Gemini generates response
       ↓
ChatResponse (message + products)
       ↓
LiveData updates
       ↓
ChatActivity displays message + product cards
```

### 2. Barcode Scanning Flow

### 2. Barcode Scanning Flow

```
User clicks "📷 Scan" in ChatActivity
       ↓
Start MainActivity with startActivityForResult
       ↓
BarcodeScannerAnalyzer detects barcode
       ↓
MainActivity.onBarcodeScanned()
       ↓
ProductViewModel.searchProductByUPC()
       ↓
ProductRepository.searchProductByUPC()
       ↓
BestBuyApiService (Retrofit API call)
       ↓
API Response → Product Model
       ↓
LiveData updates
       ↓
Navigate to ProductDetailActivity
       ↓
User exits → Return to ChatActivity
```

### 3. Product Detail Loading Flow

```
ProductDetailActivity.onCreate()
       ↓
Get SKU from Intent
       ↓
ProductViewModel.getProductBySKU()
       ↓
ProductRepository.getProductBySKU()
       ↓
Parallel API calls:
  ├─ Get Product Details
  ├─ Get Recommendations
  └─ Get Also Viewed
       ↓
Update LiveData
       ↓
Activity observes and displays data
```

## Key Component Descriptions

### View Layer (UI)

- **MainActivity**: Main screen, contains camera preview and barcode scanning
- **ProductDetailActivity**: Product detail page, displays complete product information
- **RecommendationAdapter**: RecyclerView Adapter, displays recommended products

### ViewModel Layer

- **ProductViewModel**: 
  - Manage UI states (loading, error)
  - Handle product search and recommended products loading
  - Use LiveData to notify UI updates

### Repository Layer

- **ProductRepository**: 
  - Encapsulate data sources (API)
  - Provide unified data access interface
  - Handle API errors and exceptions

### Data Layer

- **BestBuyApiService**: Retrofit API interface definition
- **RetrofitClient**: Retrofit instance configuration
- **Product**: Data model class

### Utils

- **BarcodeScannerAnalyzer**: CameraX image analyzer for barcode scanning
- **NetworkUtils**: Network status checking utility
- **FormatUtils**: Data formatting utility

## Dependency Injection

Currently using manual dependency injection (Manual DI):

```kotlin
// ViewModel creates Repository
private val repository = ProductRepository()

// Repository uses RetrofitClient
private val apiService = RetrofitClient.apiService

// Activity creates ViewModel
viewModel = ViewModelProvider(this)[ProductViewModel::class.java]
```

### Future upgrade options:

- **Hilt**: Google recommended DI framework
- **Koin**: Lightweight Kotlin DI framework

## Asynchronous Processing

Using Kotlin Coroutines:

```kotlin
// suspend function in Repository
suspend fun searchProductByUPC(upc: String): Result<Product?> {
    return withContext(Dispatchers.IO) {
        // API call
    }
}

// Using viewModelScope in ViewModel
viewModelScope.launch {
    val result = repository.searchProductByUPC(upc)
    // Update LiveData
}
```

## State Management

Using LiveData for state management:

```kotlin
// ViewModel
private val _product = MutableLiveData<Product?>()
val product: LiveData<Product?> = _product

private val _loading = MutableLiveData<Boolean>()
val loading: LiveData<Boolean> = _loading

private val _error = MutableLiveData<String?>()
val error: LiveData<String?> = _error

// Activity
viewModel.product.observe(this) { product ->
    // Update UI
}

viewModel.loading.observe(this) { isLoading ->
    // Show/hide loading indicator
}
```

## Network Layer Architecture

### Retrofit Configuration

```kotlin
Retrofit.Builder()
    .baseUrl("https://api.bestbuy.com/")
    .client(okHttpClient)
    .addConverterFactory(GsonConverterFactory.create())
    .build()
```

### OkHttp Interceptors

- **HttpLoggingInterceptor**: Logs API requests and responses
- Set connection timeout (30 seconds)

### API Service

All API calls are suspend functions that support Coroutines.

## Image Loading

Using Glide to load product images:

```kotlin
Glide.with(context)
    .load(imageUrl)
    .into(imageView)
```

## Advantages

1. **Separation of Concerns**: View, ViewModel, Repository each have their own responsibilities
2. **Testability**: Each layer can be tested independently
3. **Maintainability**: Code structure is clear and easy to maintain and extend
4. **Lifecycle Awareness**: ViewModel and LiveData automatically handle lifecycle

## Future Improvement Suggestions

1. ~~**Introduce Hilt/Koin**: Improve dependency injection~~ (Using Manual DI)
2. ✅ **Use Room**: Room Database **v4** implemented (shopping cart, user interactions, chat messages, sale price columns)
3. **StateFlow/SharedFlow**: Replace LiveData
4. **Jetpack Compose**: Use modern UI framework
5. **Clean Architecture**: Further layering (Domain Layer)
6. **Unit Tests**: Add comprehensive test coverage

---

## UCP Server Architecture (Python FastAPI)

### Overall Architecture

```
┌─────────────────────────────────────────────────────┐
│                   FastAPI App                        │
│                   (main.py)                          │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼──────┐    ┌─────────▼────────┐
│  API Routes  │    │   Middleware     │
│  /chat       │    │   (CORS, Auth)   │
│  /products   │    └──────────────────┘
│  /cart       │
│  /checkout   │
│  /orders     │
└───────┬──────┘
        │
┌───────▼───────────────────────────────────────────┐
│              ChatService                          │
│  - process_message()                              │
│  - execute_function()                             ││  - _generate_suggested_questions()                │└───────┬───────────────────────┬───────────────────┘
        │                       │
┌───────▼────────┐    ┌─────────▼────────────────────┐
│ GeminiClient   │    │  BestBuyAPIClient            │
│ - AI Dialog    │    │  - search_products()         │
│ - Function     │    │  - get_store_availability()  │
│   Calling      │    │  - get_also_bought()         │
│                │    │  - advanced_search()         │
└────────────────┘    │  - get_categories()          │
                      │  - get_complementary_products│
                      └──────────────────────────────┘
```

### Key Components

#### 1. Chat Service
- **Location**: `app/services/chat_service.py`
- **Responsibility**: 
  - Process user messages
  - Invoke Gemini AI
  - Execute function calls
  - Generate suggested question chips (`_generate_suggested_questions()`)
  - SKU-focus logic: extract up to 8 SKUs from AI response to show matched product cards
  - Return results to user

#### 2. Gemini Client
- **Location**: `app/services/gemini_client.py`
- **Features**:
  - Communicate with Gemini 2.5 Flash API
  - Handle Function Calling
  - Manage conversation history

#### 3. Best Buy API Client
- **Location**: `app/services/bestbuy_client.py`
- **Features**:
  - Product search (UPC, keywords, advanced)
  - Store inventory query (BOPIS)
  - Product recommendations (Also Viewed, Also Bought, Complementary)
  - Categories browsing (`get_categories`, `search_categories`)
  - Intelligent search optimization (specification filtering, relevance scoring)
  - `COMMON_CATEGORIES` dict for zero-latency category ID lookup
  - `CATEGORY_COMPLEMENT_MAP` for heuristic complementary product fallback

#### 4. Rate Limiter
- **Location**: `app/services/rate_limiter.py`
- **Features**: Enforces 5 req/min against Best Buy API; prevents quota exhaustion

#### 5. Additional API Routes
- `app/api/cart.py` — server-side cart management
- `app/api/checkout.py` — checkout session lifecycle
- `app/api/orders.py` — order tracking
- `app/api/products.py` — direct product endpoints

### Data Flow

```
Android App
    ↓ POST /chat
ChatService.process_message()
    ↓
GeminiClient.generate_content()
    ↓ (if function call needed)
ChatService.execute_function()
    ↓
BestBuyAPIClient.[function_name]()
    ↓
Return results → Gemini
    ↓
Gemini generates final response
    ↓
ChatResponse (message + products + function_calls)
    ↓ HTTPS Response
Android App displays results
```

### Deployment Architecture

```
Local Machine (localhost:58000)  ← Docker exposes port 58000
    ↓
Cloudflare Tunnel
    ↓
Public URL (https://ucp.rudy.xx.kg)
    ↓
Android App (anywhere in the world)
```

**Advantages**:
- ✅ HTTPS encryption
- ✅ Globally accessible
- ✅ No need for port forwarding or VPN
- ✅ DDoS protection

### Related Documents

- `ucp_server/README.md` - Complete UCP Server documentation
- `.github/copilot-instructions.md` - Development guide
- `BESTBUY_API_INTEGRATION_ANALYSIS.md` - API integration analysis
