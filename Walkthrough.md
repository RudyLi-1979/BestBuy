# Walkthrough: BestBuy Scanner App Development

## Latest Completion: Chat-First Architecture + UCP Server + New Features Implementation (2026-02-13)

### Feature Overview
Successfully restructured the application to a **Chat-First Architecture**, integrated **Gemini 2.5 Flash AI** and local **UCP Server** to provide intelligent conversational shopping experience.

### Completed Core Features

#### 1. Chat Mode Becomes Main Feature ✅
- **ChatActivity** is the application launch screen (LAUNCHER)
- **Voice Input**: Using Speech Recognition API
- **Scan Button**: Click to launch MainActivity for barcode scanning
- **Return Mechanism**: MainActivity returns to ChatActivity after scanning

#### 2. UCP Server Backend ✅
- **Framework**: Python FastAPI
- **AI Model**: Gemini 2.5 Flash
- **Features**: 
  - Chat API (`/chat`) handles conversations
  - Gemini Function Calling executes search, inventory queries, etc.
  - Intelligent search optimization (specification filtering, relevance scoring)
- **Deployment**: Cloudflare Tunnel (https://ucp.rudy.xx.kg)

#### 3. Chat Product Cards ✅
- **ChatProductAdapter**: Display product cards in chat messages
- **Horizontal RecyclerView**: Swipe through products horizontally
- **Click for Details**: Card click opens ProductDetailActivity
- **Data Source**: Product list returned from UCP Server /chat API

#### 4. New Features Implementation (2026-02-13) ✅

**Store Inventory Query (Store Availability)**
- Query product inventory at nearby physical stores
- Support ZIP code location
- Display store information, distance, inventory status
- Gemini function: `check_store_availability()`

**Also Bought Recommendations**
- Display products frequently purchased together
- Cross-selling functionality
- Increase average order value
- Gemini function: `get_also_bought()`

**Advanced Search (Advanced Search)**
- Multi-criteria filtering: manufacturer, price range, categories, shipping options, sale status
- Intelligent specification matching
- Relevance scoring and sorting
- Gemini function: `advanced_product_search()`

### Related Documents
- `.github/copilot-instructions.md` - AI Agent development guide
- `ucp_server/README.md` - UCP Server setup guide
- `BESTBUY_API_INTEGRATION_ANALYSIS.md` - Best Buy API integration analysis

---

## Phase 1: Personalized Recommendation Feature (2026-02-12)

### Feature Overview
Successfully implemented a personalized recommendation system based on user behavior that can track user interactions and generate personalized product recommendations.

### Implemented Core Features
- ✅ Automatically track user behavior (VIEW, SCAN, ADD_TO_CART)
- ✅ Analyze user's favorite product categories
- ✅ Generate personalized recommendations based on category preferences
- ✅ Filter viewed products to avoid duplicates
- ✅ Minimum interaction threshold (5) to ensure recommendation quality

### New/Modified Files

#### Data Layer (9 new files + 1 modified)
1. [`UserInteraction.kt`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/java/com/bestbuy/scanner/data/model/UserInteraction.kt) - User interaction entity
2. [`UserInteractionDao.kt`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/java/com/bestbuy/scanner/data/dao/UserInteractionDao.kt) - Data access layer
3. [`AppDatabase.kt`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/java/com/bestbuy/scanner/data/database/AppDatabase.kt) - Upgraded to v2, added Migration
4. [`UserBehaviorRepository.kt`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/java/com/bestbuy/scanner/data/repository/UserBehaviorRepository.kt) - Behavior tracking repository
5. [`RecommendationEngine.kt`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/java/com/bestbuy/scanner/data/recommendation/RecommendationEngine.kt) - Recommendation engine
6. [`RecommendationRepository.kt`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/java/com/bestbuy/scanner/data/repository/RecommendationRepository.kt) - Recommendation repository
7. [`BestBuyApiService.kt`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/java/com/bestbuy/scanner/data/api/BestBuyApiService.kt) - Added getMostViewed API

#### ViewModel & UI Layer (3 new files + 3 modified)
8. [`RecommendationViewModel.kt`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/java/com/bestbuy/scanner/ui/viewmodel/RecommendationViewModel.kt) - Recommendation ViewModel
9. [`PersonalizedRecommendationAdapter.kt`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/java/com/bestbuy/scanner/ui/adapter/PersonalizedRecommendationAdapter.kt) - Recommendation card adapter
10. [`item_recommendation_card.xml`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/res/layout/item_recommendation_card.xml) - Recommendation card layout
11. [`MainActivity.kt`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/java/com/bestbuy/scanner/ui/MainActivity.kt) - Added scan tracking
12. [`ProductDetailActivity.kt`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/java/com/bestbuy/scanner/ui/ProductDetailActivity.kt) - Added "For You" block
13. [`activity_product_detail.xml`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/res/layout/activity_product_detail.xml) - Added UI block

### Technical Highlights
- **Database Migration**: Upgraded from v1 to v2 with smooth migration and no data loss
- **Recommendation Algorithm**: Collaborative filtering based on category preferences
- **Quality Control**: Minimum interaction threshold avoids low-quality recommendations
- **User Experience**: Recommendation block automatically hides when data is insufficient

Detailed documentation:
- [`Implementation_Phase1_Recommendations.md`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/Implementation_Phase1_Recommendations.md)
- [`recommendation_quality_improvement.md`](file:///C:/Users/rudy/.gemini/antigravity/brain/7e5776d1-786a-42f7-9823-1efb21b83dcf/recommendation_quality_improvement.md)

---

## Shopping Cart Implementation

## Completed Items

### 1. Data Layer - Room Database

#### 1.1 Data Model
✅ [`CartItem.kt`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/java/com/bestbuy/scanner/data/model/CartItem.kt)
- Room Entity defines shopping cart item structure
- Contains SKU, name, price, image, quantity, and add time

#### 1.2 Data Access Layer
✅ [`CartDao.kt`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/java/com/bestbuy/scanner/data/dao/CartDao.kt)
- Provides CRUD operations
- Uses Flow for reactive data updates
- Supports query, add, update, delete, and clear shopping cart

#### 1.3 Database
✅ [`AppDatabase.kt`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/java/com/bestbuy/scanner/data/database/AppDatabase.kt)
- Room Database singleton pattern
- Version 1, contains CartItem entity

#### 1.4 Repository
✅ [`CartRepository.kt`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/java/com/bestbuy/scanner/data/repository/CartRepository.kt)
- Encapsulates data operation logic
- Automatically increases quantity if item already exists
- Automatically removes item when quantity is 0

---

### 2. ViewModel Layer

✅ [`CartViewModel.kt`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/java/com/bestbuy/scanner/ui/viewmodel/CartViewModel.kt)
- Manages shopping cart UI state
- Provides LiveData:
  - `cartItems`: List of shopping cart items
  - `itemCount`: Total item count
  - `totalPrice`: Total price (automatically calculated)
- Provides operation methods:
  - `addToCart()`: Add item
  - `updateQuantity()`: Update quantity
  - `removeItem()`: Remove item
  - `clearCart()`: Clear shopping cart

---

### 3. UI Layer

#### 3.1 Shopping Cart Main Screen
✅ [`activity_cart.xml`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/res/layout/activity_cart.xml)
- RecyclerView displays shopping cart items
- Empty state message (when shopping cart is empty)
- Bottom bar displays total price
- Clear Cart and Checkout buttons

✅ [`CartActivity.kt`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/java/com/bestbuy/scanner/ui/CartActivity.kt)
- Observes ViewModel data changes
- Handles item quantity adjustment
- Confirmation dialog (removing item, clearing shopping cart)
- Checkout dialog (displays total price, reminds testing app)

#### 3.2 Shopping Cart Item
✅ [`item_cart.xml`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/res/layout/item_cart.xml)
- Item image, name, unit price
- Quantity control buttons (+/-)
- Remove button
- Subtotal display

✅ [`CartAdapter.kt`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/java/com/bestbuy/scanner/ui/adapter/CartAdapter.kt)
- RecyclerView Adapter
- DiffUtil optimizes list update
- Handles quantity change and remove events

---

### 4. Integration with Existing Features

#### 4.1 ProductDetailActivity Update
✅ [`ProductDetailActivity.kt`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/java/com/bestbuy/scanner/ui/ProductDetailActivity.kt)

**Before:**
```kotlin
binding.btnAddToCart.setOnClickListener {
    val url = product.addToCartUrl ?: product.productUrl
    if (url != null) {
        val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
        startActivity(intent)
    }
}
```

**After:**
```kotlin
binding.btnAddToCart.setOnClickListener {
    cartViewModel.addToCart(product)
    
    Snackbar.make(binding.root, "Added to cart", Snackbar.LENGTH_LONG)
        .setAction("View Cart") {
            startActivity(Intent(this, CartActivity::class.java))
        }
        .show()
}
```

#### 4.2 MainActivity 更新
✅ [`MainActivity.kt`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/java/com/bestbuy/scanner/ui/MainActivity.kt)
- 新增購物車圖標到 Toolbar
- 點擊圖標導航至 CartActivity

✅ [`menu_main.xml`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/res/menu/menu_main.xml)
- 定義 Toolbar 選單

#### 4.3 AndroidManifest
✅ [`AndroidManifest.xml`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/AndroidManifest.xml)
- 註冊 CartActivity

---

### 5. Dependencies

✅ [`build.gradle.kts`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/build.gradle.kts)
- 新增 KSP plugin
- 新增 Room 依賴:
  - `room-runtime`
  - `room-ktx`
  - `room-compiler` (KSP)

---

## 功能特點 (Features)

### ✅ 核心功能
1. **新增商品到購物車**
   - 點擊「Add to Cart」按鈕
   - 顯示 Snackbar 確認訊息
   - 可直接點擊「View Cart」查看購物車

2. **查看購物車**
   - 從 MainActivity Toolbar 點擊購物車圖標
   - 顯示所有已新增的商品
   - 即時顯示總金額

3. **調整商品數量**
   - 點擊 + 按鈕增加數量
   - 點擊 - 按鈕減少數量
   - 數量為 0 時自動移除商品
   - 小計即時更新

4. **移除商品**
   - 點擊垃圾桶圖標
   - 顯示確認對話框
   - 確認後移除商品

5. **清空購物車**
   - 點擊「Clear Cart」按鈕
   - 顯示確認對話框
   - 確認後清空所有商品

6. **結帳(測試)**
   - 點擊「Checkout」按鈕
   - 顯示總金額
   - 提示為測試 App,無真實金流
   - 確認後清空購物車

### ✅ 資料持久化
- 使用 Room Database 儲存
- 關閉 App 後資料仍保留
- 重新開啟 App 時購物車內容恢復

### ✅ UI/UX 優化
- Material Design 風格
- 空狀態提示
- 確認對話框防止誤操作
- Snackbar 即時回饋
- 響應式資料更新

---

## 驗證步驟 (Verification Steps)

### 1. 建置專案
```powershell
cd c:\Users\rudy\AndroidStudioProjects\BestBuy
.\gradlew build
```

### 2. 手動測試流程

#### 測試 1: 新增商品到購物車
1. 啟動 App
2. 掃描任意商品條碼
3. 進入商品詳情頁
4. 點擊「Add to Cart」按鈕
5. ✅ 確認出現 Snackbar 提示「Added to cart」
6. ✅ 確認 Snackbar 有「View Cart」按鈕

#### 測試 2: 查看購物車
1. 點擊 MainActivity Toolbar 的購物車圖標
2. ✅ 確認進入 CartActivity
3. ✅ 確認顯示剛才新增的商品
4. ✅ 確認商品資訊正確(圖片、名稱、價格、數量=1)
5. ✅ 確認底部顯示正確總金額

#### 測試 3: 調整數量
1. 在購物車內點擊「+」按鈕
2. ✅ 確認數量變為 2
3. ✅ 確認小計更新為 價格 × 2
4. ✅ 確認總金額更新
5. 點擊「-」按鈕
6. ✅ 確認數量變為 1
7. ✅ 確認小計和總金額更新

#### 測試 4: 移除商品
1. 點擊商品的垃圾桶圖標
2. ✅ 確認出現確認對話框
3. 點擊「Remove」
4. ✅ 確認商品從列表移除
5. ✅ 確認總金額更新

#### 測試 5: 清空購物車
1. 新增多個商品到購物車
2. 點擊「Clear Cart」按鈕
3. ✅ 確認出現確認對話框
4. 點擊「Clear」
5. ✅ 確認所有商品被移除
6. ✅ 確認顯示空狀態畫面

#### 測試 6: 資料持久化
1. 新增商品到購物車
2. 完全關閉 App(從最近使用的 App 列表滑掉)
3. 重新開啟 App
4. 點擊購物車圖標
5. ✅ 確認購物車商品仍然存在

#### 測試 7: 結帳功能
1. 新增商品到購物車
2. 進入購物車頁面
3. 點擊「Checkout」按鈕
4. ✅ 確認出現對話框顯示總金額
5. ✅ 確認提示「This is a demo app. No actual payment will be processed.」
6. 點擊「OK」
7. ✅ 確認購物車被清空
8. ✅ 確認返回 MainActivity

---

## 技術亮點 (Technical Highlights)

### 1. MVVM 架構
- 清晰的職責分離
- ViewModel 管理 UI 狀態
- Repository 封裝資料操作
- LiveData 實現響應式更新

### 2. Room Database
- 類型安全的資料庫操作
- Flow 支援響應式查詢
- 自動處理資料庫遷移

### 3. Material Design
- 使用 MaterialCardView
- Material Button
- Snackbar 回饋
- 符合 Android 設計規範

### 4. 智慧數量管理
- 重複新增同商品時自動增加數量
- 數量為 0 時自動移除
- 避免資料冗餘

---

## 檔案變更清單 (File Changes)

| 檔案 | 類型 | 說明 |
|------|------|------|
| `CartItem.kt` | 新增 | Room Entity 資料模型 |
| `CartDao.kt` | 新增 | Room DAO 介面 |
| `AppDatabase.kt` | 新增 | Room Database 單例 |
| `CartRepository.kt` | 新增 | 購物車資料操作 Repository |
| `CartViewModel.kt` | 新增 | 購物車 ViewModel |
| `activity_cart.xml` | 新增 | 購物車主畫面佈局 |
| `item_cart.xml` | 新增 | 購物車商品項目佈局 |
| `CartAdapter.kt` | 新增 | RecyclerView Adapter |
| `CartActivity.kt` | 新增 | 購物車 Activity |
| `menu_main.xml` | 新增 | MainActivity 選單 |
| `ProductDetailActivity.kt` | 修改 | 整合本地購物車功能 |
| `MainActivity.kt` | 修改 | 新增購物車圖標和導航 |
| `AndroidManifest.xml` | 修改 | 註冊 CartActivity |
| `build.gradle.kts` | 修改 | 新增 Room 依賴 |

---

## 後續改進建議

1. **購物車數量 Badge**: 在 Toolbar 購物車圖標上顯示商品數量
2. **商品詳情快速查看**: 在購物車內點擊商品可查看詳情
3. **訂單歷史**: 記錄已結帳的訂單
4. **優惠券系統**: 支援折扣碼輸入
5. **商品收藏**: 新增 Wishlist 功能
6. **庫存檢查**: 整合 BestBuy API 檢查商品庫存
7. **價格追蹤**: 記錄價格變動歷史
8. **分享購物車**: 支援分享購物車內容
---

## Bug 修復與功能增強 (Bug Fixes & Enhancements)

### 已修復的問題

#### 1. 產品詳情頁旋轉資料遺失
**問題**: 旋轉裝置時，產品詳情頁面會重新載入並顯示空白
**原因**: `onCreate` 中的 `savedInstanceState == null` 檢查阻止了資料重新載入
**解決方案**:
- 移除 `savedInstanceState` 檢查
- 在 `AndroidManifest.xml` 中為 `ProductDetailActivity` 添加 `android:configChanges="orientation|screenSize|keyboardHidden"`
- 確保 Activity 在配置變更時不會被重新創建

#### 2. 推薦商品點擊無法導航
**問題**: 點擊推薦商品後無法跳轉到該商品的詳細頁面
**根本原因**: 
1. SKU 類型不匹配 - `RecommendationProduct.sku` 是 `String`，但 Intent 使用 `getIntExtra` 讀取
2. JSON 解析錯誤 - API 返回單一 `Product` 物件，但程式碼期待 `ProductResponse` 包含 `products` 陣列

**解決方案**:
- 修改 `ProductDetailActivity.onCreate`:
  - 將 `getIntExtra("PRODUCT_SKU", -1)` 改為 `getStringExtra("PRODUCT_SKU")`
  - 更新條件判斷為 `!productSku.isNullOrEmpty()`
- 修改 `BestBuyApiService.getProductBySKU`:
  - 返回類型從 `Response<ProductResponse>` 改為 `Response<Product>`
- 修改 `ProductRepository.getProductBySKU`:
  - 解析邏輯從 `response.body()?.products?.firstOrNull()` 改為 `response.body()`

#### 3. 購物車商品圖片裁切問題
**問題**: 購物車中的商品圖片被裁切，無法完整顯示
**解決方案**: 在 `item_cart.xml` 中將 `ImageView` 的 `scaleType` 從 `centerCrop` 改為 `fitCenter` 並添加 padding

#### 4. 減號按鈕圖示不一致
**問題**: 減號按鈕圖示與加號按鈕粗細不一致
**解決方案**: 更新 `ic_minus.xml`，將 `strokeWidth` 從 1.5 改為 2.5，使其與加號圖示一致

### 新增功能

#### 1. 購物車商品點擊導航
**功能**: 點擊購物車中的商品可跳轉到該商品的詳細頁面
**實現**:
- 在 `CartAdapter` 添加 `onItemClicked` 回調參數
- 在 `CartActivity` 中處理點擊事件，使用 `PRODUCT_SKU` Intent extra 導航到 `ProductDetailActivity`
- 將 `CartItem.sku` (Int) 轉換為 String: `item.sku.toString()`

---

## 後續改進建議

1. **購物車數量 Badge**: 在 Toolbar 購物車圖標上顯示商品數量
2. ~~**商品詳情快速查看**: 在購物車內點擊商品可查看詳情~~ ✅ 已完成
3. **訂單歷史**: 記錄已結帳的訂單
4. **優惠券系統**: 支援折扣碼輸入
5. **商品收藏**: 新增 Wishlist 功能
6. **庫存檢查**: 整合 BestBuy API 檢查商品庫存
7. **價格追蹤**: 記錄價格變動歷史
8. **分享購物車**: 支援分享購物車內容
