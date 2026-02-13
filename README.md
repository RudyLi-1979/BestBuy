# BestBuy Scanner App

一個功能完整的 **Chat-First** Android 購物應用程式，整合 **Gemini 2.5 Flash AI**、**Best Buy API** 和本地 **UCP Server**，提供智能對話購物體驗。

## 🎯 核心特色

### 💬 Chat Mode（主要功能）
- **AI 智能助手**: 整合 Gemini 2.5 Flash，自然語言購物對話
- **產品卡片顯示**: 聊天中直接顯示產品照片、價格和詳情
- **語音輸入**: 支援語音搜尋產品
- **多功能整合**: 在對話中完成搜尋、查詢庫存、加入購物車等操作
- **本地 UCP Server**: Python FastAPI 後端，處理 AI 對話和 Best Buy API 整合

### 📱 傳統功能
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
- 🏪 **門市庫存查詢**: 查詢附近實體門市的產品庫存（BOPIS）
- 🛍️ **Also Bought 推薦**: 顯示經常一起購買的商品
- 🔍 **進階搜尋**: 多條件篩選（製造商、價格範圍、運送選項等）
- 🔄 **螢幕旋轉支援**: 旋轉裝置時保留產品資訊
- 🌐 **Cloudflare Tunnel**: 全球可訪問的 UCP Server 連線

## 技術架構

### Android App
- **語言**: Kotlin
- **架構模式**: MVVM (Model-View-ViewModel)
- **UI**: XML Layouts with View Binding
- **相機**: CameraX
- **條碼掃描**: ML Kit Barcode Scanning
- **網路請求**: Retrofit + OkHttp
- **圖片載入**: Glide
- **資料持久化**: Room Database v2
- **非同步處理**: Kotlin Coroutines + Flow
- **依賴注入**: Manual DI

### UCP Server (Python Backend)
- **框架**: FastAPI
- **AI 模型**: Gemini 2.5 Flash
- **資料庫**: SQLite (開發) / PostgreSQL (生產)
- **API 整合**: Best Buy Developer API
- **部署**: Cloudflare Tunnel (HTTPS)
- **非同步**: asyncio + httpx

## 專案結構

```
📁 BestBuy/
├── 📱 app/ (Android App)
│   └── src/main/java/com/bestbuy/scanner/
│       ├── data/
│       │   ├── api/
│       │   │   ├── BestBuyApiService.kt      # API 介面定義
│       │   │   ├── UCPApiService.kt          # UCP Server API
│       │   │   ├── RetrofitClient.kt         # Retrofit 配置
│       │   │   └── UCPRetrofitClient.kt      # UCP Client
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
│       ├── ui/
│       │   ├── adapter/
│       │   │   ├── ChatAdapter.kt            # 聊天訊息 Adapter
│       │   │   ├── ChatProductAdapter.kt     # 聊天產品卡片
│       │   │   ├── RecommendationAdapter.kt  # 推薦商品 Adapter
│       │   │   ├── PersonalizedRecommendationAdapter.kt
│       │   │   └── CartAdapter.kt            # 購物車 Adapter
│       │   ├── viewmodel/
│       │   │   ├── ChatViewModel.kt          # 聊天 ViewModel
│       │   │   ├── ProductViewModel.kt       # 產品 ViewModel
│       │   │   ├── CartViewModel.kt          # 購物車 ViewModel
│       │   │   └── RecommendationViewModel.kt
│       │   ├── ChatActivity.kt           # 主畫面 (Chat Mode)
│       │   ├── MainActivity.kt           # 掃描畫面
│       │   ├── ProductDetailActivity.kt  # 產品詳情頁
│       │   └── CartActivity.kt           # 購物車頁面
│
├── 🐍 ucp_server/ (Python Backend)
│   ├── app/
│   │   ├── main.py                       # FastAPI 入口
│   │   ├── config.py                     # 配置
│   │   ├── models/                       # 資料模型
│   │   ├── schemas/                      # Pydantic 驗證
│   │   ├── services/
│   │   │   ├── bestbuy_client.py         # Best Buy API Client
│   │   │   ├── gemini_client.py          # Gemini AI Client
│   │   │   └── chat_service.py           # Chat 處理服務
│   │   └── api/
│   │       └── chat.py                   # Chat API 端點
│   ├── requirements.txt
│   └── README.md
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

**Android App:**
- Android Studio Arctic Fox 或更新版本
- Android SDK 24 或以上
- BestBuy API Key ([註冊取得](https://developer.bestbuy.com/))

**UCP Server:**
- Python 3.11+
- pip (Python 套件管理器)
- Gemini API Key

### 2. 設定 Android App

#### 2.1 設定 Best Buy API Key

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

#### 2.2 建置 Android 專案

```bash
# 克隆專案後，在 Android Studio 中開啟
# 等待 Gradle 同步完成

# 或使用命令列建置
./gradlew build
```

### 3. 設定 UCP Server

#### 3.1 安裝依賴

**使用 Docker（推薦）：**
```bash
cd ucp_server

# 配置環境變數
copy .env.example .env
# 編輯 .env 填入 API Keys

# 啟動服務
.\start_docker.ps1
# 或使用 docker-compose up -d
```

**本地開發模式：**
```bash
cd ucp_server

# 建立虛擬環境
python -m venv venv

# 啟動虛擬環境 (Windows)
.\venv\Scripts\activate

# 啟動虛擬環境 (Linux/Mac)
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt
```
**Docker 模式：**
```bash
# 使用快速腳本
.\start_docker.ps1

# 或直接使用 docker-compose
docker-compose up -d

# 查看日誌
docker-compose logs -f
```

**本地模式：**
```bash
# 使用 PowerShell 腳本
.\start_server.ps1

# 或直接使用 uvicorn
uvicorn app.main:app --reload --port 58000
```

Server 將在 `http://localhost:5_API_KEY
# GEMINI_API_KEY=你的Gemini_API_KEY
```

#### 3.3 啟動 Server

```bash
# 開發模式
uvicorn app.main:app --reload --port 8000

# 或使用提供的腳本
.\start_server.ps1
```

Server 將在 `http://localhost:8000` 啟動。

#### 3.4 Cloudflare Tunnel (可選)

如果需要從實體裝置存取 UCP Server，可以使用 Cloudflare Tunnel：

```bash
# 安裝 cloudflared
# 查看 ucp_server/README.md 了解詳細設定
```

### 4. 執行應用程式

1. 連接 Android 裝置或啟動模擬器
2. 點擊 Android Studio 的 "Run" 按鈕
3. 授予相機權限
4. 開始掃描條碼！

## 使用方式

### Chat Mode (主要功能)

1. 開啟應用程式，自動進入 Chat Mode
2. 輸入文字或使用語音搜尋產品
   - 例：「我想買 iPhone 15 Pro」
   - 例：「Show me MacBook Pro 14 inch」
   - 例：「哪裡可以買到 Mac mini?」
3. AI 助手會對話式回答並顯示產品卡片
4. 點擊產品卡片查看完整詳情
5. 在詳情頁可以加入購物車或查看更多資訊

### 掃描條碼

1. 在 Chat Mode 中點擊「📷 Scan」按鈕
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

### ✨ Chat-First 架構重構 + UCP Server 整合 (2026-02-13)

**Chat Mode 成為主要功能：**
- ✅ ChatActivity 為應用程式主畫面
- ✅ 語音輸入支援（Speech Recognition API）
- ✅ 掃描按鈕啟動 MainActivity
- ✅ 聊天中顯示產品卡片，點擊查看詳情

**UCP Server 後端：**
- ✅ Python FastAPI + Gemini 2.5 Flash 整合
- ✅ 智能搜尋優化（規格篩選、關聯性評分）
- ✅ Cloudflare Tunnel 全球可訪問
- ✅ 對話歷史管理
- ✅ 函式呼叫（Function Calling）

**新功能 (2026-02-13)：**
- ✅ **門市庫存查詢**: 查詢附近實體門市的產品庫存（BOPIS）
- ✅ **Also Bought 推薦**: 顯示經常一起購買的商品
- ✅ **進階搜尋**: 多條件篩選（製造商、價格範圍、運送選項、特價等）

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

**相關文件：**
- [Walkthrough.md](Walkthrough.md) - 完整開發歷程
- [ARCHITECTURE.md](ARCHITECTURE.md) - 架構說明
- [SECURITY.md](SECURITY.md) - API Key 安全指南

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
