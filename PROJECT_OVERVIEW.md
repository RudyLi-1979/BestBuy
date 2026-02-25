# BestBuy Scanner - Project Overview

## Project Summary

An intelligent shopping assistant Android application that combines barcode scanning, AI-powered chat, and product recommendations, integrating Best Buy API with Gemini 2.5 Flash AI through a local UCP Server.

---

## Key Features

### 1. Chat-First Interface
- **AI Shopping Assistant**: Natural language product search powered by Gemini 2.5 Flash
- **Voice Input**: Speech recognition for hands-free shopping
- **Product Cards**: Visual product display within chat messages
- **Smart Recommendations**: Context-aware product suggestions

### 2. Barcode Scanning
- **Real-time Scanning**: CameraX + ML Kit for instant barcode recognition
- **Multi-format Support**: UPC-A, EAN-13, UPC-E (8-14 digits)
- **Quick Access**: One-tap scan button from chat interface

### 3. Shopping Cart
- **Local Storage**: Room Database for offline persistence
- **Quantity Management**: Add, update, remove items
- **Price Calculation**: Real-time total with quantity adjustments
- **Product Details**: Tap to view full information
- **Toolbar Badge**: Cart icon with live item count + total amount in ChatActivity Toolbar
- **Always-Visible Summary**: Bottom bar always shows item count and total (shows 0 / $0.00 when empty)

### 4. Personalized Recommendations
- **Behavior Tracking**: Automatically tracks views, scans, and cart additions
- **Category Analysis**: Identifies user preferences by product categories
- **Smart Filtering**: Excludes previously viewed items
- **Quality Control**: Minimum 5 interactions before recommendations

### 5. Store Inventory (BOPIS)
- **Location-based Search**: Find nearby stores with product availability
- **Pickup Options**: Check in-store pickup eligibility
- **Store Details**: Address, phone, distance, and hours

### 6. Advanced Search
- **Multi-criteria Filtering**: Manufacturer, price range, category, shipping
- **Specification Matching**: Intelligent filtering by storage, color, model
- **Relevance Scoring**: AI-powered result ranking

### 7. Chat History Persistence
- **Local-First History**: Chat messages (including product cards) stored to Room DB locally
- **Product Card Preservation**: Product cards survive app restart — serialized as JSON with Gson and stored in `ChatMessageEntity.productsJson`
- **Session-Scoped**: Messages grouped by `sessionId`, independently queryable and clearable
- **Offline History**: History loaded from local DB without requiring a server round-trip

---

## System Architecture

### Three-Tier Architecture

```
┌───────────────────────────────────┐
│   Android App (Client)            │
│  - Kotlin MVVM Pattern            │
│  - CameraX + ML Kit               │
│  - Room Database                  │
└──────────┬────────────────────────┘
           │ HTTPS (REST API)
           │ Port: 58000
┌──────────▼────────────────────────┐
│   UCP Server (Middleware)         │
│ - Python FastAPI Framework        │
│ - Gemini 2.5 Flash Integration    │
│ - Docker Containerized            │
└──────────┬────────────────────────┘
           │ HTTPS (REST API)
           │ Rate Limit: 5 req/s
┌──────────▼────────────────────────┐
│  Best Buy Developer API (Service) │
│ - Product Information             │
│ - Store Inventory                 │
│ - Recommendations                 │
└───────────────────────────────────┘
```

---

## Component Interactions

### 1. Android App → UCP Server

**Chat Mode Flow:**
```
User Message
    ↓
ChatActivity → ChatViewModel → ChatRepository
    ↓
POST /chat (HTTPS)
    ↓
UCP Server receives request
```

**Scan Mode Flow:**
```
Barcode Scanned
    ↓
MainActivity → ProductViewModel → ProductRepository
    ↓
Direct call to Best Buy API (UPC search)
    ↓
Display ProductDetailActivity
```

### 2. UCP Server → Gemini AI

**AI Processing:**
```
/chat endpoint receives user message
    ↓
ChatService.process_message()
    ↓
GeminiClient.generate_content()
    ↓
Gemini analyzes intent & decides function call
    ↓
Returns: AI response + function_calls array
```

**Function Calling:**
```
Gemini determines: "search_products"
    ↓
ChatService.execute_function()
    ↓
BestBuyAPIClient.search_products()
    ↓
Results returned to Gemini
    ↓
Gemini generates natural language response
```

### 3. UCP Server → Best Buy API

**API Methods:**
- `search_products(query)` → Product search
- `get_product_by_sku(sku)` → Product details
- `search_by_upc(upc)` → Barcode lookup
- `get_store_availability(sku, zip)` → Store inventory
- `get_also_bought(sku)` → Cross-sell recommendations
- `advanced_search(filters)` → Multi-criteria search

**Rate Limiting:**
- 5 requests per second (enforced by RateLimiter)
- 50,000 requests per day (Best Buy API limit)

---

## Technology Stack

### Android App
| Component | Technology |
|-----------|-----------|
| Language | Kotlin |
| Architecture | MVVM (Manual DI) |
| Camera | CameraX 1.3.1 |
| Barcode | ML Kit 17.2.0 |
| Networking | Retrofit 2.9.0 + OkHttp 4.12.0 |
| Database | Room Database v4 |
| Async | Coroutines 1.7.3 + Flow |
| Image Loading | Glide 4.16.0 |
| UI | XML Layouts + View Binding |
| Chat Persistence | Room DB (`ChatMessageEntity`) + Gson (products as JSON) |

### UCP Server
| Component | Technology |
|-----------|-----------|
| Framework | FastAPI 0.109.0 |
| AI Model | Gemini 2.5 Flash |
| HTTP Client | httpx 0.26.0 |
| Database | SQLite (Dev) / PostgreSQL (Prod) |
| Deployment | Docker + docker-compose |
| Runtime | Python 3.11 |
| Server | Uvicorn (ASGI) |

### External Services
| Service | Purpose |
|---------|---------|
| Best Buy API | Product data, inventory, recommendations |
| Gemini API | Natural language processing, function calling |
| Cloudflare Tunnel | Secure HTTPS access (optional) |

---

## Data Flow Diagrams

### Chat Mode with AI

```
User: "I want to buy Mac mini 256GB"
    ↓
Android App (ChatActivity)
    ↓ POST /chat
UCP Server (ChatService)
    ↓
Gemini AI (Intent Analysis)
    ↓ Function Call: advanced_product_search(query="mac mini 256GB")
UCP Server (BestBuyAPIClient)
    ↓
Best Buy API (Search + Filter)
    ↓
Results: [Mac mini M2 256GB, Mac mini M2 Pro 256GB, ...]
    ↓
Gemini AI (Generate Response)
    ↓
UCP Server Returns: {message: "...", products: [...]}
    ↓
Android App Displays: AI message + Product cards
```

### Barcode Scanning

```
User: Scans barcode "190199246850"
    ↓
MainActivity (BarcodeScannerAnalyzer)
    ↓
ProductViewModel.searchProductByUPC()
    ↓
ProductRepository → BestBuyApiService
    ↓
GET /v1/products(upc=190199246850)
    ↓
Best Buy API Returns: Apple AirPods Pro
    ↓
Navigate to ProductDetailActivity
    ↓
Display: Product info + Recommendations + "For You" section
```

### Store Availability Check

```
User: "Where can I buy iPhone 15 near 94103?"
    ↓
Gemini extracts: product="iPhone 15", zip="94103"
    ↓
Function Call: check_store_availability(sku, zip)
    ↓
UCP Server → Best Buy Stores API
    ↓
Returns: [Store 1, Store 2, Store 3] with inventory status
    ↓
Gemini formats response with store details
    ↓
User sees: Store locations, distance, availability
```

---

## API Endpoints

### Android App APIs (Direct to Best Buy)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/products(upc={upc})` | GET | Search by barcode |
| `/v1/products/{sku}` | GET | Get product details |
| `/v1/products/{sku}/alsoViewed` | GET | Also viewed products |
| `/v1/products/mostViewed` | GET | Trending products |

### UCP Server APIs (Android → UCP)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/chat` | POST | Send chat message to AI |
| `/chat/session/{id}/history` | GET | Get conversation history |
| `/chat/session/{id}` | DELETE | Clear conversation |
| `/cart` | POST | Add item to server-side cart |
| `/cart/{session_id}` | GET | Get cart contents |
| `/checkout` | POST | Create checkout session |
| `/checkout/{id}` | PUT | Update checkout session |
| `/checkout/{id}/complete` | POST | Complete checkout |
| `/orders/{id}` | GET | Get order details |
| `/` | GET | Health check |

### UCP Server APIs (UCP → Best Buy)

| Method | Purpose |
|--------|---------|
| `search_products(query)` | General product search |
| `search_by_upc(upc)` | Barcode lookup |
| `get_product_by_sku(sku)` | Product details |
| `get_store_availability(sku, zip)` | Store inventory (BOPIS) |
| `get_also_bought(sku)` | Cross-sell recommendations |
| `get_recommendations(sku)` | Also-viewed recommendations |
| `get_similar_products(sku)` | Similar product suggestions |
| `advanced_search(filters)` | Multi-criteria search |
| `get_categories(parent_id)` | Browse product categories |
| `search_categories(name)` | Search categories by name |
| `get_complementary_products(sku, category_id)` | Category-map fallback when alsoBought is empty |

---

## Key Innovations

### 1. Smart Search Optimization
- **Specification Extraction**: Automatically identifies storage (256GB), colors, models
- **Relevance Scoring**: Ranks products by exact match (100) vs partial match (50)
- **Spec Filtering**: Removes products missing user-specified requirements

### 2. AI Function Calling
- **Intent Detection**: Gemini determines user needs from natural language
- **Multi-step Queries**: Single message can trigger multiple API calls
- **Context Awareness**: Maintains conversation history for follow-up questions

### 3. Hybrid Recommendation Engine
- **Best Buy API**: Also Viewed, Also Bought (collaborative filtering)
- **Local Analysis**: User behavior tracking (content-based filtering)
- **Combined Output**: Personalized "For You" section with category preferences

### 4. Docker Deployment
- **One-command Startup**: `.\start_docker.ps1` launches entire backend
- **Hot Reload**: Code changes automatically reflected without restart
- **Data Persistence**: SQLite database and keys survive container restarts

---

## Performance Metrics

### API Rate Limits
- **Best Buy API**: 5 requests/second, 50,000 requests/day
- **RateLimiter**: Automatic throttling to prevent quota exhaustion
- **Retry Logic**: Exponential backoff on rate limit errors

### Response Times
- **Barcode Scan**: ~1-2 seconds (API call + rendering)
- **Chat Query**: ~2-4 seconds (Gemini + Best Buy API + rendering)
- **Store Availability**: ~3-5 seconds (multiple API calls for stores)

### Data Storage
- **Room Database**: Local SQLite for cart items, user interactions
- **Cache Strategy**: No caching (always fresh data from Best Buy)
- **Offline Support**: Cart persists offline, syncs on reconnect

---

## Deployment Architecture

### Development Environment
```
Local Machine
    ├── Android Studio (App Development)
    ├── Docker Desktop (UCP Server)
    └── VS Code (Python Backend)
```

### Production Environment (Conceptual)
```
Mobile Devices
    ↓ HTTPS
Cloudflare Tunnel / Nginx
    ↓
Docker Container (UCP Server)
    ↓
Best Buy API (External)
Gemini API (External)
```

---

## Security Considerations

### API Key Management
- ✅ Environment variables (`.env` files)
- ✅ BuildConfig for Android (not hardcoded)
- ✅ `.gitignore` prevents accidental commits
- ❌ No encryption at rest (development only)

### Network Security
- ✅ HTTPS for all external API calls
- ✅ Cloudflare Tunnel for secure access
- ❌ No authentication/authorization (POC stage)
- ❌ No API key rotation mechanism

### Data Privacy
- ✅ Local-only storage (no user accounts)
- ✅ No personal data collected
- ✅ Minimal logging (no sensitive data)
- ⚠️ Conversation history stored locally (can be cleared)

---

## Future Enhancements

### Phase 2: Advanced Features
- [ ] User accounts with cloud sync
- [ ] Price tracking and alerts
- [ ] Wishlist with sharing
- [ ] Product comparison view
- [ ] Order history tracking

### Phase 3: ML/AI Improvements
- [ ] Custom recommendation model training
- [ ] Image-based product search
- [ ] Natural language checkout
- [ ] Predictive inventory alerts

### Phase 4: Enterprise Features
- [ ] Multi-store support (Target, Walmart, Amazon)
- [ ] B2B bulk ordering
- [ ] Analytics dashboard
- [ ] Admin panel for UCP Server

---

## Project Statistics

- **Total Files**: 150+
- **Lines of Code**: ~15,000
- **Development Time**: ~3 weeks
- **Languages**: Kotlin (Android), Python (Backend)
- **APIs Integrated**: 2 (Best Buy, Gemini)
- **Docker Images**: 1 (UCP Server)

---

## References

- **Best Buy API Documentation**: https://bestbuyapis.github.io/api-documentation/
- **Gemini AI Documentation**: https://ai.google.dev/docs
- **CameraX Documentation**: https://developer.android.com/training/camerax
- **ML Kit Barcode Scanning**: https://developers.google.com/ml-kit/vision/barcode-scanning

---

**Last Updated**: February 25, 2026  
**Version**: 1.1.0  
**License**: Educational Use Only
