# BestBuy Scanner App

一個功能完整的 Android 條碼掃描應用程式，整合 BestBuy API 來顯示產品資訊和推薦商品。

## 功能特色

- 📷 **條碼掃描**: 使用 CameraX 和 ML Kit 進行即時條碼掃描
- 🔍 **產品搜尋**: 透過 UPC 條碼搜尋 BestBuy 產品
- 📊 **產品詳情**: 顯示完整的產品資訊，包括：
  - 產品名稱、製造商、型號
  - 價格資訊（含特價顯示）
  - 產品圖片
  - 詳細說明
  - 庫存狀態
  - 顧客評價
  - 運送資訊
- 🎯 **推薦商品**: 顯示相關推薦產品，點擊可查看詳細資訊
- 👀 **其他人也看了**: 顯示其他顧客瀏覽的產品
- ✨ **個人化推薦 (For You)**: 基於用戶瀏覽歷史的智能推薦
  - 自動追蹤用戶行為（瀏覽、掃描、加入購物車）
  - 分析用戶最喜歡的商品類別
  - 基於類別偏好生成個人化推薦
  - 過濾已瀏覽商品避免重複
  - 最小互動次數門檻（5次）確保推薦品質
- 🛒 **本地購物車**: 完整的購物車管理功能
  - 新增商品到購物車
  - 調整商品數量（+/-）
  - 移除單一商品或清空購物車
  - 即時顯示總金額
  - 點擊購物車商品可查看詳細資訊
  - 資料持久化（使用 Room Database）
- 🔄 **螢幕旋轉支援**: 旋轉裝置時保留產品資訊
- 🔗 **購物連結**: 直接連結到 BestBuy 網站進行購買

## 技術架構

- **語言**: Kotlin
- **架構模式**: MVVM (Model-View-ViewModel)
- **UI**: XML Layouts with View Binding
- **相機**: CameraX
- **條碼掃描**: ML Kit Barcode Scanning
- **網路請求**: Retrofit + OkHttp
- **圖片載入**: Glide
- **資料持久化**: Room Database
- **非同步處理**: Kotlin Coroutines + Flow
- **依賴注入**: Manual DI (可升級至 Hilt/Koin)

## 專案結構

```
app/
├── src/main/java/com/bestbuy/scanner/
│   ├── data/
│   │   ├── api/
│   │   │   ├── BestBuyApiService.kt      # API 介面定義
│   │   │   └── RetrofitClient.kt         # Retrofit 配置
│   │   ├── dao/
│   │   │   ├── CartDao.kt                # 購物車資料存取層
│   │   │   └── UserInteractionDao.kt     # 用戶互動資料存取層
│   │   ├── database/
│   │   │   └── AppDatabase.kt            # Room Database (v2)
│   │   ├── model/
│   │   │   ├── Product.kt                # 產品資料模型
│   │   │   ├── CartItem.kt               # 購物車項目資料模型
│   │   │   └── UserInteraction.kt        # 用戶互動資料模型
│   │   ├── recommendation/
│   │   │   └── RecommendationEngine.kt   # 推薦引擎
│   │   └── repository/
│   │       ├── ProductRepository.kt      # 產品資料儲存庫
│   │       ├── CartRepository.kt         # 購物車資料儲存庫
│   │       ├── UserBehaviorRepository.kt # 用戶行為儲存庫
│   │       └── RecommendationRepository.kt # 推薦儲存庫
│   ├── ui/
│   │   ├── adapter/
│   │   │   ├── RecommendationAdapter.kt  # 推薦商品 Adapter
│   │   │   ├── PersonalizedRecommendationAdapter.kt # 個人化推薦 Adapter
│   │   │   └── CartAdapter.kt            # 購物車 Adapter
│   │   ├── viewmodel/
│   │   │   ├── ProductViewModel.kt       # 產品 ViewModel
│   │   │   ├── CartViewModel.kt          # 購物車 ViewModel
│   │   │   └── RecommendationViewModel.kt # 推薦 ViewModel
│   │   ├── MainActivity.kt               # 主畫面 (掃描)
│   │   ├── ProductDetailActivity.kt      # 產品詳情頁
│   │   └── CartActivity.kt               # 購物車頁面
│   └── utils/
│       └── BarcodeScannerAnalyzer.kt     # 條碼掃描分析器
└── src/main/res/
    ├── layout/
    │   ├── activity_main.xml             # 主畫面佈局
    │   ├── activity_product_detail.xml   # 產品詳情佈局
    │   ├── activity_cart.xml             # 購物車佈局
    │   ├── item_product_recommendation.xml # 推薦商品項目
    │   ├── item_recommendation_card.xml   # 個人化推薦卡片
    │   └── item_cart.xml                 # 購物車商品項目
    └── values/
        ├── colors.xml
        ├── strings.xml
        └── themes.xml
```

## 安裝與設定

### 1. 前置需求

- Android Studio Arctic Fox 或更新版本
- Android SDK 24 或以上
- BestBuy API Key ([註冊取得](https://developer.bestbuy.com/))

### 2. 設定 API Key

在專案根目錄的 `.env` 檔案中，將 `YOUR_API_KEY_HERE` 替換為你的 BestBuy API Key：

```bash
# .env
BESTBUY_API_KEY=你的實際API_KEY
```

如果 `.env` 檔案不存在，請複製 `.env.example` 並重新命名為 `.env`：

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

**安全提示**: `.env` 檔案已加入 `.gitignore`，確保你的 API Key 不會被提交到版本控制系統。

### 3. 建置專案

```bash
# 克隆專案後，在 Android Studio 中開啟
# 等待 Gradle 同步完成

# 或使用命令列建置
./gradlew build
```

### 4. 執行應用程式

1. 連接 Android 裝置或啟動模擬器
2. 點擊 Android Studio 的 "Run" 按鈕
3. 授予相機權限
4. 開始掃描條碼！

## 使用方式

### 掃描條碼

1. 開啟應用程式
2. 授予相機權限
3. 將相機對準商品條碼
4. 應用程式會自動掃描並搜尋產品
5. 找到產品後自動跳轉到詳情頁

### 手動輸入

如果無法掃描條碼，可以點擊「手動輸入 UPC」按鈕，直接輸入產品的 UPC 代碼。

### 瀏覽產品詳情

- 查看產品圖片、價格、說明
- 查看推薦商品和其他人也看了的商品
- 點擊推薦商品可查看更多產品
- 點擊「在 BestBuy 查看」可前往官網
- 點擊「加入購物車」可直接購買

## BestBuy API 使用說明

### API 端點

本應用程式使用以下 BestBuy API 端點：

1. **產品搜尋 (UPC)**
   - `GET /v1/products(upc={upc})?apiKey={key}`
   - 透過 UPC 條碼搜尋產品

2. **產品詳情 (SKU)**
   - `GET /v1/products/{sku}.json?apiKey={key}`
   - 透過 SKU 取得產品詳細資訊

3. **推薦商品**
   - `GET /v1/products/{sku}/recommendations.json?apiKey={key}`
   - 取得產品的推薦商品列表

4. **Also Viewed (其他人也看了)**
   - `GET /v1/products/{sku}/alsoViewed.json?apiKey={key}`
   - 取得其他顧客瀏覽的相關產品

### API 限制

- 免費版 API 有請求限制（每秒 5 次，每天 50,000 次）
- 請勿在生產環境中硬編碼 API Key
- 建議使用環境變數或安全的密鑰管理系統

## 權限說明

應用程式需要以下權限：

- `CAMERA`: 用於掃描條碼
- `INTERNET`: 用於存取 BestBuy API
- `ACCESS_NETWORK_STATE`: 檢查網路連線狀態

## 支援的條碼格式

ML Kit 支援以下條碼格式：
- UPC-A 和 UPC-E
- EAN-8 和 EAN-13
- Code-39
- Code-93
- Code-128
- ITF
- Codabar
- QR Code
- Data Matrix
- PDF417
- Aztec

## 常見問題

### Q: 掃描條碼後沒有找到產品？

A: 可能的原因：
1. 產品不在 BestBuy 資料庫中
2. UPC 代碼不正確
3. 網路連線問題
4. API Key 未正確設定

### Q: 相機無法啟動？

A: 請確認：
1. 已授予相機權限
2. 裝置有可用的相機
3. 沒有其他應用程式正在使用相機

### Q: 推薦商品沒有顯示？

A: BestBuy API 並非所有產品都有推薦商品資料，這是正常現象。

## 最新更新

### ✨ 階段一：個人化推薦功能 (2026-02-12)

成功實現基於用戶行為的個人化推薦系統：

**核心功能：**
- ✅ 自動追蹤用戶行為（VIEW, SCAN, ADD_TO_CART）
- ✅ 分析用戶最喜歡的商品類別
- ✅ 基於類別偏好生成個人化推薦
- ✅ 過濾已瀏覽商品避免重複
- ✅ 最小互動次數門檻（5次）確保推薦品質

**技術實現：**
- Room Database v2（新增 UserInteraction 表）
- RecommendationEngine（推薦演算法）
- UserBehaviorRepository（行為追蹤）
- "For You" UI 區塊（個人化推薦顯示）

詳細資訊請參考：
- `Implementation_Phase1_Recommendations.md` - 實作計畫
- `personalized_recommendation_research.md` - 研究文件
- `recommendation_quality_improvement.md` - 品質改進說明

## 未來改進方向

- [x] 個人化推薦系統（階段一已完成）
- [ ] 協同過濾推薦（階段二）
- [ ] 機器學習模型整合（階段三）
- [ ] 加入產品比較功能
- [ ] 支援歷史記錄
- [ ] 加入最愛清單
- [ ] 支援價格追蹤和通知
- [ ] 整合更多電商平台 API
- [ ] 加入深色模式
- [ ] 支援多語言
- [ ] 優化 UI/UX 設計
- [ ] 加入快取機制減少 API 請求

## 授權

本專案僅供學習和參考使用。

## 相關連結

- [BestBuy API 文件](https://bestbuyapis.github.io/api-documentation/)
- [ML Kit Barcode Scanning](https://developers.google.com/ml-kit/vision/barcode-scanning)
- [CameraX](https://developer.android.com/training/camerax)
- [Retrofit](https://square.github.io/retrofit/)

## 聯絡方式

如有問題或建議，歡迎提出 Issue 或 Pull Request。

---

**注意**: 請確保遵守 BestBuy API 的使用條款和限制。
