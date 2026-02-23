# BestBuy Scanner App

A full-featured **Chat-First** Android shopping application that integrates **Gemini 2.5 Flash AI**, the **Best Buy API**, and a local **UCP Server** to provide an intelligent conversational shopping experience.

## 🎯 Core Features

### 💬 Chat Mode (Main Feature)
- **AI Assistant**: Integrated with Gemini 2.5 Flash for natural language shopping conversations
- **Product Card Display**: Directly shows product photos, prices, and details within the chat
- **Voice Input**: Supports voice search for products
- **Multi-functional Integration**: Complete actions like searching, checking inventory, and adding to cart within the conversation
- **Local UCP Server**: A Python FastAPI backend that handles AI conversations and Best Buy API integration

### 📱 Traditional Features
- 📷 **Barcode Scanning**: Real-time barcode scanning using CameraX and ML Kit
- 🔍 **Product Search**: Search for BestBuy products via UPC barcode
- 📊 **Product Details**: Displays complete product information, including:
  - Product name, manufacturer, model number
  - Price information (including sale price display)
  - Product images
  - Detailed description
  - Stock status
  - Customer reviews
  - Shipping information
- 🎯 **Recommended Products**: Displays related recommended products, clickable for more details
- 👀 **Also Viewed**: Shows products viewed by other customers
- ✨ **Personalized Recommendations (For You)**: Smart recommendations based on user browsing history
  - Automatically tracks user behavior (viewing, scanning, adding to cart)
  - Analyzes the user's favorite product categories
  - Generates personalized recommendations based on category preferences
  - Filters out previously viewed items to avoid repetition
  - A minimum interaction threshold (5 times) ensures recommendation quality
- 🛒 **Local Shopping Cart**: Complete shopping cart management functionality
  - Add items to the shopping cart
  - Adjust item quantity (+/-)
  - Remove a single item or clear the entire cart
  - Real-time display of the total amount
  - Click on a cart item to view its details
  - Data persistence (using Room Database)
- 🏪 **Store Inventory Check**: Check product inventory at nearby physical stores (BOPIS)
- 🛍️ **Also Bought Recommendations**: Displays items frequently bought together
- 🔍 **Advanced Search**: Multi-condition filtering (manufacturer, price range, shipping options, etc.)
- 🔄 **Screen Rotation Support**: Retains product information when the device is rotated
- 🌐 **Cloudflare Tunnel**: Globally accessible UCP Server connection

## Technical Architecture

### Android App
- **Language**: Kotlin
- **Architecture Pattern**: MVVM (Model-View-ViewModel)
- **UI**: XML Layouts with View Binding
- **Camera**: CameraX
- **Barcode Scanning**: ML Kit Barcode Scanning
- **Networking**: Retrofit + OkHttp
- **Image Loading**: Glide
- **Data Persistence**: Room Database v2
- **Asynchronous Processing**: Kotlin Coroutines + Flow
- **Dependency Injection**: Manual DI

### UCP Server (Python Backend)
- **Framework**: FastAPI
- **AI Model**: Gemini 2.5 Flash
- **Database**: SQLite (Development) / PostgreSQL (Production)
- **API Integration**: Best Buy Developer API
- **Deployment**: Cloudflare Tunnel (HTTPS)
- **Asynchronous**: asyncio + httpx

## Project Structure

```
📁 BestBuy/
├── 📱 app/ (Android App)
│   └── src/main/java/com/bestbuy/scanner/
│       ├── data/
│       │   ├── api/
│       │   │   ├── BestBuyApiService.kt      # API Interface Definition
│       │   │   ├── UCPApiService.kt          # UCP Server API
│       │   │   ├── RetrofitClient.kt         # Retrofit Configuration
│       │   │   └── UCPRetrofitClient.kt      # UCP Client
│   │   ├── dao/
│   │   │   ├── CartDao.kt                # Cart Data Access Object
│   │   │   └── UserInteractionDao.kt     # User Interaction Data Access Object
│   │   ├── database/
│   │   │   └── AppDatabase.kt            # Room Database (v2)
│   │   ├── model/
│   │   │   ├── Product.kt                # Product Data Model
│   │   │   ├── CartItem.kt               # Cart Item Data Model
│   │   │   └── UserInteraction.kt        # User Interaction Data Model
│   │   ├── recommendation/
│   │   │   └── RecommendationEngine.kt   # Recommendation Engine
│   │   └── repository/
│   │       ├── ProductRepository.kt      # Product Data Repository
│   │       ├── CartRepository.kt         # Cart Data Repository
│   │       ├── UserBehaviorRepository.kt # User Behavior Repository
│   │       └── RecommendationRepository.kt # Recommendation Repository
│       ├── ui/
│       │   ├── adapter/
│       │   │   ├── ChatAdapter.kt            # Chat Message Adapter
│       │   │   ├── ChatProductAdapter.kt     # Chat Product Card
│       │   │   ├── RecommendationAdapter.kt  # Recommended Product Adapter
│       │   │   ├── PersonalizedRecommendationAdapter.kt
│       │   │   └── CartAdapter.kt            # Cart Adapter
│       │   ├── viewmodel/
│       │   │   ├── ChatViewModel.kt          # Chat ViewModel
│       │   │   ├── ProductViewModel.kt       # Product ViewModel
│       │   │   ├── CartViewModel.kt          # Cart ViewModel
│       │   │   └── RecommendationViewModel.kt
│       │   ├── ChatActivity.kt           # Main Screen (Chat Mode)
│       │   ├── MainActivity.kt           # Scanner Screen
│       │   ├── ProductDetailActivity.kt  # Product Detail Page
│       │   └── CartActivity.kt           # Cart Page
│
├── 🐍 ucp_server/ (Python Backend)
│   ├── app/
│   │   ├── main.py                       # FastAPI Entrypoint
│   │   ├── config.py                     # Configuration
│   │   ├── models/                       # Data Models
│   │   ├── schemas/                      # Pydantic Schemas
│   │   ├── services/
│   │   │   ├── bestbuy_client.py         # Best Buy API Client
│   │   │   ├── gemini_client.py          # Gemini AI Client
│   │   │   └── chat_service.py           # Chat Processing Service
│   │   └── api/
│   │       └── chat.py                   # Chat API Endpoint
│   ├── requirements.txt
│   └── README.md
│   └── utils/
│       └── BarcodeScannerAnalyzer.kt     # Barcode Scanning Analyzer
└── src/main/res/
    ├── layout/
    │   ├── activity_main.xml             # Main screen layout
    │   ├── activity_product_detail.xml   # Product detail layout
    │   ├── activity_cart.xml             # Cart layout
    │   ├── item_product_recommendation.xml # Recommended product item
    │   ├── item_recommendation_card.xml   # Personalized recommendation card
    │   └── item_cart.xml                 # Cart item layout
    └── values/
        ├── colors.xml
        ├── strings.xml
        └── themes.xml
```

## Setup and Configuration

### 1. Prerequisites

**Android App:**
- Android Studio Arctic Fox or later version
- Android SDK 24 or higher
- BestBuy API Key ([Register to Get](https://developer.bestbuy.com/))

**UCP Server:**
- Python 3.11+
- pip (Python Package Manager)
- Gemini API Key

### 2. Configure Android App

#### 2.1 Configure Best Buy API Key

In the `.env` file at the project root, replace `YOUR_API_KEY_HERE` with your BestBuy API Key:

```bash
# .env
BESTBUY_API_KEY=your_actual_API_KEY
```

If the `.env` file does not exist, copy `.env.example` and rename it to `.env`:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

**Security Note**: The `.env` file has been added to `.gitignore` to ensure your API Key will not be committed to the version control system.

#### 2.2 Build Android Project

```bash
# After cloning the project, open in Android Studio
# Wait for Gradle sync to complete

# Or use command line to build
./gradlew build
```

### 3. Configure UCP Server

#### 3.1 Install Dependencies

**Using Docker (Recommended):**
```bash
cd ucp_server

# Configure environment variables
copy .env.example .env
# Edit .env to fill in API Keys

# Start service
.\start_docker.ps1
# Or use docker-compose up -d
```

**Local Development Mode:**
```bash
cd ucp_server

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\activate

# Activate virtual environment (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Docker Mode:**
```bash
# Use quick script
.\start_docker.ps1

# Or use docker-compose directly
docker-compose up -d

# View logs
docker-compose logs -f
```

**Local Mode:**
```bash
# Use PowerShell script
.\start_server.ps1

# Or use uvicorn directly
uvicorn app.main:app --reload --port 58000
```

**Server will start at `http://localhost:58000`.**

**Environment Configuration:**
```bash
# Configure in ucp_server/.env
BESTBUY_API_KEY=your_bestbuy_api_key
# GEMINI_API_KEY=your_gemini_api_key
```

#### 3.3 Start Server

```bash
# Development mode
uvicorn app.main:app --reload --port 8000

# Or use the provided script
.\start_server.ps1
```

The server will start at `http://localhost:8000`.

#### 3.4 Cloudflare Tunnel (Optional)

If you need to access the UCP Server from physical devices, you can use Cloudflare Tunnel:

```bash
# Install cloudflared
# See ucp_server/README.md for detailed configuration
```

### 4. Run Application

1. Connect Android device or start emulator
2. Click "Run" button in Android Studio
3. Grant camera permissions
4. Start scanning barcodes!

## Usage

### Chat Mode (Main Feature)

1. Open the app, automatically enter Chat Mode
2. Input text or use voice to search for products
   - Example: "I want to buy iPhone 15 Pro"
   - Example: "Show me MacBook Pro 14 inch"
   - Example: "Where can I buy Mac mini?"
3. AI assistant will answer conversationally and display product cards
4. Click product cards to view complete details
5. On detail page, add to cart or view more information

### Scan Barcode

1. In Chat Mode, click the '📷 Scan' button
2. Grant camera permissions
3. Point camera at product barcode
4. The app will automatically scan and search for products
5. After finding product, automatically navigate to detail page

### Manual Input

If you cannot scan a barcode, you can click the 'Manual Input UPC' button to directly input the product's UPC code.

### View Product Details

- View product images, prices, and descriptions
- View recommended products and items viewed by others
- Click recommended products to view more items
- Click 'View on BestBuy' to go to the official website
- Click 'Add to Cart' to make a direct purchase

## BestBuy API Usage Guide

### API Endpoints

This application uses the following BestBuy API endpoints:

1. **Product Search (UPC)**
   - `GET /v1/products(upc={upc})?apiKey={key}`
   - Search for products via UPC barcode

2. **Product Details (SKU)**
   - `GET /v1/products/{sku}.json?apiKey={key}`
   - Get detailed product information via SKU

3. **Product Recommendations**
   - `GET /v1/products/{sku}/recommendations.json?apiKey={key}`
   - Get the product's recommendation list

4. **Also Viewed (Other Customers Viewed)**
   - `GET /v1/products/{sku}/alsoViewed.json?apiKey={key}`
   - Get related products viewed by other customers

### API Limits

- Free tier API has request limits (5 requests per second, 50,000 per day)
- Do not hardcode the API Key in production environment
- It is recommended to use environment variables or a secure key management system

## Permissions Description

The application requires the following permissions:

- `CAMERA`: Used to scan barcodes
- `INTERNET`: Used to access BestBuy API
- `ACCESS_NETWORK_STATE`: Check network connection status

## Supported Barcode Formats

ML Kit supports the following barcode formats:
- UPC-A and UPC-E
- EAN-8 and EAN-13
- Code-39
- Code-93
- Code-128
- ITF
- Codabar
- QR Code
- Data Matrix
- PDF417
- Aztec

## FAQ

### Q: Product not found after scanning barcode?

A: Possible reasons:
1. Product is not in the BestBuy database
2. UPC code is incorrect
3. Network connection issues
4. API Key is not properly configured

### Q: Camera cannot start?

A: Please confirm:
1. Camera permissions are granted
2. Device has an available camera
3. No other applications are using the camera

### Q: Recommended products are not displayed?

A: BestBuy API does not have recommendation data for all products, this is normal.

## Latest Updates

### ✨ Chat-First Architecture Restructure + UCP Server Integration (2026-02-13)

**Chat Mode Becomes Main Feature:**
- ✅ ChatActivity is the main screen of the app
- ✅ Voice input support (Speech Recognition API)
- ✅ Scan button launches MainActivity
- ✅ Display product cards in chat, click to view details

**UCP Server Backend:**
- ✅ Python FastAPI + Gemini 2.5 Flash Integration
- ✅ Intelligent search optimization (specification filtering, relevance scoring)
- ✅ Cloudflare Tunnel globally accessible
- ✅ Chat history management
- ✅ Function Calling

**New Features (2026-02-13):**
- ✅ **Store Inventory Query**: Query product inventory at nearby physical stores (BOPIS)
- ✅ **Also Bought Recommendations**: Display products frequently purchased together
- ✅ **Advanced Search**: Multi-criteria filtering (manufacturer, price range, shipping options, special offers, etc.)

### ✨ Phase 1: Personalized Recommendation Feature (2026-02-12)

Successfully implemented a personalized recommendation system based on user behavior:

**Core Features:**
- ✅ Automatically track user behavior (VIEW, SCAN, ADD_TO_CART)
- ✅ Analyze user's favorite product categories
- ✅ Generate personalized recommendations based on category preferences
- ✅ Filter viewed products to avoid duplicates
- ✅ Minimum interaction threshold (5 times) to ensure recommendation quality

**Technical Implementation:**
- Room Database v2 (Added UserInteraction table)
- RecommendationEngine (Recommendation algorithm)
- UserBehaviorRepository (Behavior tracking)
- 'For You' UI Block (Personalized recommendation display)

**Related Documents:**
- [Walkthrough.md](Walkthrough.md) - Complete development history
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture description
- [SECURITY.md](SECURITY.md) - API Key security guide

## Future Improvements

- [x] Personalized recommendation system (Phase 1 completed)
- [ ] Collaborative filtering recommendations (Phase 2)
- [ ] Machine learning model integration (Phase 3)
- [ ] Add product comparison feature
- [ ] Support browsing history
- [ ] Add favorites list
- [ ] Support price tracking and notifications
- [ ] Integrate more e-commerce platform APIs
- [ ] Add dark mode
- [ ] Support multiple languages
- [ ] Optimize UI/UX design
- [ ] Add caching mechanism to reduce API requests

## License

This project is for learning and reference purposes only.

## Related Links

- [BestBuy API Documentation](https://bestbuyapis.github.io/api-documentation/)
- [ML Kit Barcode Scanning](https://developers.google.com/ml-kit/vision/barcode-scanning)
- [CameraX](https://developer.android.com/training/camerax)
- [Retrofit](https://square.github.io/retrofit/)

## Contact

If you have any questions or suggestions, feel free to submit an Issue or Pull Request.

---

**Note**: Please ensure you comply with BestBuy API's terms of service and restrictions.
