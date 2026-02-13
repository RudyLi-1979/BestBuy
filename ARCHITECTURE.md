# 專案架構說明

## 整體架構

本專案採用 **Chat-First 架構**，包含 Android App 和 UCP Server 兩個部分：

```
┌─────────────────────────────────────────────────────┐
│                   Android App                        │
│                 (Kotlin + MVVM)                     │
│                                                      │
│  ChatActivity (主畫面) ──┐                          │
│      ↓                    │                          │
│  ChatViewModel            │                          │
│      ↓                    │                          │
│  ChatRepository ──────────┼──→ UCP Server           │
│                           │                          │
│  MainActivity (掃描) ─────┘                          │
│  ProductDetailActivity                              │
│  CartActivity                                       │
└──────────────────┬──────────────────────────────────┘
                   │ HTTPS (Cloudflare Tunnel)
                   │
┌──────────────────▼──────────────────────────────────┐
│                 UCP Server                           │
│             (Python + FastAPI)                      │
│                                                      │
│  /chat API                                          │
│      ↓                                              │
│  ChatService                                        │
│      ↓                                              │
│  ┌──────────────┐  ┌────────────────────────┐     │
│  │ Gemini 2.5   │  │ BestBuyAPIClient       │     │
│  │ Flash Client │  │ - search_products()    │     │
│  │              │  │ - get_store_availability()│  │
│  │ Function     │  │ - get_also_bought()    │     │
│  │ Calling      │  │ - advanced_search()    │     │
│  └──────────────┘  └────────────────────────┘     │
└─────────────────────────────────────────────────────┘
```

## Android App MVVM 架構

本專案採用 MVVM (Model-View-ViewModel) 架構模式：

```
┌─────────────────────────────────────────────────────┐
│                      View Layer                      │
│  (Activity, Fragment, XML Layouts)                  │
│                                                      │
│  - ChatActivity.kt (主畫面)                         │
│  - MainActivity.kt (掃描)                           │
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

## 資料流程

### 1. Chat Mode 對話流程 (新)

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

### 2. 條碼掃描流程

### 2. 條碼掃描流程

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

### 3. 產品詳情載入流程

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

## 關鍵元件說明

### View Layer (UI)

- **MainActivity**: 主畫面，包含相機預覽和條碼掃描
- **ProductDetailActivity**: 產品詳情頁，顯示完整產品資訊
- **RecommendationAdapter**: RecyclerView Adapter，顯示推薦商品

### ViewModel Layer

- **ProductViewModel**: 
  - 管理 UI 狀態（loading, error）
  - 處理產品搜尋和推薦商品載入
  - 使用 LiveData 通知 UI 更新

### Repository Layer

- **ProductRepository**: 
  - 封裝資料來源（API）
  - 提供統一的資料存取介面
  - 處理 API 錯誤和例外

### Data Layer

- **BestBuyApiService**: Retrofit API 介面定義
- **RetrofitClient**: Retrofit 實例配置
- **Product**: 資料模型類別

### Utils

- **BarcodeScannerAnalyzer**: CameraX 圖像分析器，用於條碼掃描
- **NetworkUtils**: 網路狀態檢查工具
- **FormatUtils**: 資料格式化工具

## 依賴注入

目前使用手動依賴注入（Manual DI）：

```kotlin
// ViewModel 建立 Repository
private val repository = ProductRepository()

// Repository 使用 RetrofitClient
private val apiService = RetrofitClient.apiService

// Activity 建立 ViewModel
viewModel = ViewModelProvider(this)[ProductViewModel::class.java]
```

### 未來可升級為：

- **Hilt**: Google 推薦的 DI 框架
- **Koin**: 輕量級 Kotlin DI 框架

## 非同步處理

使用 Kotlin Coroutines：

```kotlin
// Repository 中的 suspend function
suspend fun searchProductByUPC(upc: String): Result<Product?> {
    return withContext(Dispatchers.IO) {
        // API call
    }
}

// ViewModel 中使用 viewModelScope
viewModelScope.launch {
    val result = repository.searchProductByUPC(upc)
    // Update LiveData
}
```

## 狀態管理

使用 LiveData 進行狀態管理：

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

## 網路層架構

### Retrofit 配置

```kotlin
Retrofit.Builder()
    .baseUrl("https://api.bestbuy.com/")
    .client(okHttpClient)
    .addConverterFactory(GsonConverterFactory.create())
    .build()
```

### OkHttp 攔截器

- **HttpLoggingInterceptor**: 記錄 API 請求和回應
- 設定連線超時時間（30 秒）

### API 服務

所有 API 呼叫都是 suspend functions，支援 Coroutines。

## 圖片載入

使用 Glide 載入產品圖片：

```kotlin
Glide.with(context)
    .load(imageUrl)
    .into(imageView)
```

## 優點

1. **關注點分離**: View、ViewModel、Repository 各司其職
2. **可測試性**: 各層可獨立測試
3. **維護性**: 程式碼結構清晰，易於維護和擴展
4. **生命週期感知**: ViewModel 和 LiveData 自動處理生命週期

## 後續改進建議

1. ~~**引入 Hilt/Koin**: 改善依賴注入~~ (使用 Manual DI)
2. ✅ **使用 Room**: Room Database v2 已實作（購物車、用戶互動）
3. **StateFlow/SharedFlow**: 替代 LiveData
4. **Jetpack Compose**: 使用現代 UI 框架
5. **Clean Architecture**: 進一步分層（Domain Layer）
6. **單元測試**: 加入完整的測試覆蓋

---

## UCP Server 架構 (Python FastAPI)

### 整體架構

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
│  (/chat)     │    │   (CORS, Auth)   │
└───────┬──────┘    └──────────────────┘
        │
┌───────▼───────────────────────────────────────────┐
│              ChatService                          │
│  - process_message()                              │
│  - execute_function()                             │
└───────┬───────────────────────┬───────────────────┘
        │                       │
┌───────▼────────┐    ┌─────────▼─────────────────┐
│ GeminiClient   │    │  BestBuyAPIClient        │
│ - AI Dialog    │    │  - search_products()     │
│ - Function     │    │  - get_store_availability│
│   Calling      │    │  - get_also_bought()     │
│                │    │  - advanced_search()     │
└────────────────┘    └──────────────────────────┘
```

### 關鍵組件

#### 1. Chat Service
- **位置**: `app/services/chat_service.py`
- **職責**: 
  - 處理用戶訊息
  - 調用 Gemini AI
  - 執行函數調用
  - 返回結果給用戶

#### 2. Gemini Client
- **位置**: `app/services/gemini_client.py`
- **功能**:
  - 與 Gemini 2.5 Flash API 通訊
  - 處理 Function Calling
  - 管理對話歷史

#### 3. Best Buy API Client
- **位置**: `app/services/bestbuy_client.py`
- **功能**:
  - 商品搜尋（UPC、關鍵字、進階）
  - 門市庫存查詢
  - 推薦商品（Also Viewed, Also Bought）
  - 智能搜尋優化（規格篩選、關聯性評分）

### 資料流程

```
Android App
    ↓ POST /chat
ChatService.process_message()
    ↓
GeminiClient.generate_content()
    ↓ (如需函數調用)
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

### 部署架構

```
Local Machine (localhost:8000)
    ↓
Cloudflare Tunnel
    ↓
Public URL (https://ucp.rudy.xx.kg)
    ↓
Android App (anywhere in the world)
```

**優點**:
- ✅ HTTPS 加密
- ✅ 全球可訪問
- ✅ 無需端口轉發或 VPN
- ✅ DDoS 防護

### 相關文件

- `ucp_server/README.md` - UCP Server 完整說明
- `.github/copilot-instructions.md` - 開發指南
- `BESTBUY_API_INTEGRATION_ANALYSIS.md` - API 整合分析
