# 專案架構說明

## MVVM 架構

本專案採用 MVVM (Model-View-ViewModel) 架構模式：

```
┌─────────────────────────────────────────────────────┐
│                      View Layer                      │
│  (Activity, Fragment, XML Layouts)                  │
│                                                      │
│  - MainActivity.kt                                  │
│  - ProductDetailActivity.kt                         │
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

### 1. 條碼掃描流程

```
User scans barcode
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
MainActivity observes changes
       ↓
Navigate to ProductDetailActivity
```

### 2. 產品詳情載入流程

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

1. **引入 Hilt/Koin**: 改善依賴注入
2. **使用 Room**: 加入本地資料庫快取
3. **StateFlow/SharedFlow**: 替代 LiveData
4. **Jetpack Compose**: 使用現代 UI 框架
5. **Clean Architecture**: 進一步分層（Domain Layer）
6. **單元測試**: 加入完整的測試覆蓋
