# 推薦系統技術文件

> **最後更新：2026-02-24**  
> 描述 BestBuy Scanner App 的個人化推薦機制，包含配件推薦（Sparky-like）與相關商品推薦的完整判斷流程。

---

## 目錄

1. [系統架構概覽](#1-系統架構概覽)
2. [資料收集：用戶行為追蹤](#2-資料收集用戶行為追蹤)
3. [行為摘要建構（UserBehaviorContext）](#3-行為摘要建構userbehaviorcontext)
4. [推薦觸發條件](#4-推薦觸發條件)
5. [配件推薦流程（get_complementary_products）](#5-配件推薦流程get_complementary_products)
6. [類別配對對應表](#6-類別配對對應表)
7. [API 配額管理](#7-api-配額管理)
8. [Gemini AI 整合](#8-gemini-ai-整合)
9. [完整請求流程圖](#9-完整請求流程圖)
10. [相關檔案索引](#10-相關檔案索引)

---

## 1. 系統架構概覽

```
Android App (Kotlin)                   UCP Server (Python FastAPI)
─────────────────────                  ───────────────────────────
ChatActivity                           ChatService.process_message()
  │                                      │
  ├─ UserBehaviorRepository              ├─ [Intent Detection] _is_accessory_intent()
  │    └─ Room DB (UserInteraction)      │
  │         ↓                           ├─ [Proactive Fetch] get_complementary_products()
  │   UserBehaviorContext                │    ├─ alsoBought API (Call 1)
  │   {                                  │    └─ search_products() (Call 2, 視需要)
  │     recentCategories: [...]          │
  │     recentSkus: [...]               ├─ Gemini 2.5 Flash
  │     favoriteManufacturers: [...]    │    └─ build_system_instruction(user_context)
  │     interactionCount: N             │         → 個人化 prompt 注入
  │   }                                 │
  └──────── ChatRequest ────────────→  └─ Response: { message, products[] }
```

推薦機制分兩個層次：
- **行為層**：Android Room DB 記錄用戶的瀏覽/掃描/加入購物車行為
- **推薦層**：UCP Server 根據行為資料呼叫 BestBuy API 取得真實在售商品

---

## 2. 資料收集：用戶行為追蹤

### 觸發時機

| 動作 | 觸發位置 | InteractionType |
|------|----------|-----------------|
| 進入產品詳情頁 | `ProductDetailActivity.onCreate()` | `VIEW` |
| 掃描 UPC 條碼並找到產品 | `MainActivity` → `recommendationViewModel.trackScan()` | `SCAN` |
| 點擊「加入購物車」 | `ProductDetailActivity` → `recommendationViewModel.trackAddToCart()` | `ADD_TO_CART` |

### 儲存結構（Room DB — `user_interactions` 表）

```
UserInteraction {
  id:              Int (auto)
  sku:             String      ← 產品編號
  productName:     String
  category:        String?     ← 取自 categoryPath[0].name（如 "Televisions"）
  manufacturer:    String?     ← 如 "Samsung"、"Apple"
  price:           Double
  interactionType: String
  timestamp:       Long        ← System.currentTimeMillis()
}
```

### 資料保留

- 預設保留 30 天（`cleanOldData(daysToKeep = 30)`）
- 資料存在設備本地，不上傳伺服器

---

## 3. 行為摘要建構（UserBehaviorContext）

每次用戶送出聊天訊息時，`ChatRepository.sendMessage()` 會呼叫 `UserBehaviorRepository.getBehaviorSummary()` 即時建構摘要。

### 建構邏輯

```kotlin
// 若完全沒有互動記錄 → 不注入 context（節省 Gemini token）
if (count == 0) return null

UserBehaviorContext(
  recentCategories      = dao.getMostViewedCategories(3),  // 依頻率排序的前 3 類別
  recentSkus            = dao.getRecentSkus(5),            // 依時間排序的最近 5 個 SKU
  favoriteManufacturers = dao.getTopManufacturers(2),      // 依頻率排序的前 2 品牌
  interactionCount      = dao.getTotalCount()
)
```

### 傳遞至 Server

`UserBehaviorContext` 序列化後附加在每個 `ChatRequest` 的 `user_context` 欄位中：

```json
{
  "message": "what accessories should I get?",
  "session_id": "...",
  "user_context": {
    "recent_categories": ["Televisions", "Home Theater"],
    "recent_skus": ["6537375", "6532276"],
    "favorite_manufacturers": ["Samsung", "Sony"],
    "interaction_count": 8
  }
}
```

---

## 4. 推薦觸發條件

### 條件 A：主動偵測（Proactive Fetch）

`chat_service.py` 的 `_is_accessory_intent()` 掃描用戶訊息中的關鍵詞：

```
accessories / accessory / what else / what should I get
goes with / go with / pair with / complement
complete my setup / what accessories / for it / for this
soundbar / mount / cable / case / bag / stand
enhance / upgrade / add to / bundle ...
```

**若偵測到配件意圖 AND `user_context.recent_skus` 不為空：**

→ Server 不等 Gemini 決定，直接預先呼叫 `get_complementary_products()`  
→ 把取得的真實商品名稱與價格注入 Gemini system instruction  
→ Gemini 收到指令後必須正面介紹這些商品，不得說「找不到推薦」

### 條件 B：Gemini 自主判斷（Proactive AI）

即使用戶沒有明確詢問配件，Gemini 被指示在找到主商品後主動呼叫 `get_complementary_products()`，體現 **Ecosystem Selling**（生態圈銷售）策略：

```
「You are not just a search engine — you are a knowledgeable store associate.
After finding a product the user is interested in, ALWAYS call
get_complementary_products(sku) to fetch what else goes well with it.」
```

---

## 5. 配件推薦流程（get_complementary_products）

### API 呼叫預算：最多 2 次（嚴格遵守 5 req/min 限制）

```
┌─────────────────────────────────────────────────────────────┐
│  get_complementary_products(sku, category_hints, mfr_hint)  │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
 ╔═══════════════════════╗
 ║  Call 1: alsoBought   ║  GET /v1/products/{sku}/alsoBought
 ║  BestBuy 30天         ║  → BestBuy 自家「一起購買」信號
 ║  「一起購買」資料     ║
 ╚═══════════════════════╝
         │
         ▼
   ┌─────────────┐
   │ 結果 ≥ 3 筆? │
   └──────┬──────┘
    YES ◄─┘└─► NO
     │          │
     ▼          ▼
  直接返回   ╔══════════════════════════════════╗
  （節省     ║  Call 2: search_products()       ║
  1 次 API） ║  用 CATEGORY_NAME_TO_QUERIES 查  ║
             ║  出適合的搜尋詞，一次搜尋         ║
             ║  例："Televisions" → "soundbar   ║
             ║        speaker"                  ║
             ╚══════════════════════════════════╝
                        │
                        ▼
                    返回合併結果
                    (最多 6 筆)
```

### category_hints 的優先順序

`category_hints` 直接來自 `user_context.recent_categories`（Android Room DB），**不需要額外 API call 查詢 SKU 的分類**，這是節省配額的關鍵設計。

```python
# Proactive fetch 時傳入 hints
arguments = {
    "sku": "6537375",
    "category_hints": ["Televisions"],  ← 直接來自 Room DB，0 額外 API call
    "manufacturer_hint": "Samsung",
}
```

---

## 6. 類別配對對應表

### CATEGORY_NAME_TO_QUERIES（字串型類別 → 搜尋詞）

用於 `search_products()` fallback，覆蓋 50+ 種類別關鍵字：

| 用戶瀏覽類別 | 配件搜尋詞 |
|------------|-----------|
| Televisions / TV / OLED / QLED | `soundbar speaker` |
| Monitors | `monitor stand webcam` |
| Laptops / MacBooks | `laptop bag USB hub` |
| Desktops | `monitor keyboard mouse` |
| Tablets / iPads | `tablet case keyboard` |
| Cell Phones / iPhones | `phone case wireless earbuds` |
| Headphones / Earbuds | `headphone stand audio cable` |
| Cameras / DSLR | `camera memory card camera bag` |
| Gaming / Game Consoles / PlayStation / Xbox | `gaming headset controller` |
| Printers | `printer ink cartridge paper` |

### CATEGORY_COMPLEMENT_MAP（分類 ID → 分類 ID，保留作參考）

舊版設計，對應 BestBuy 官方 category ID，目前已被 `CATEGORY_NAME_TO_QUERIES` 取代（後者不需要額外 API call 查詢分類 ID）。

---

## 7. API 配額管理

### BestBuy 免費開發者帳號限制

| 限制類型 | 數量 |
|---------|------|
| 每分鐘請求數 | **5 次** |
| 每日請求數 | 50,000 次 |

### RateLimiter 實作（滑動視窗）

```python
# rate_limiter.py
class RateLimiter:
    WINDOW = 60.0  # 60 秒滑動視窗

    async def acquire(self):
        # 計算 60 秒內已用的 request 數
        # 若 >= 5，等待最舊一筆記錄超出視窗後再繼續
```

### 每次 Chat 訊息的 API 消耗預算

| 情境 | API 呼叫次數 |
|------|------------|
| 普通商品搜尋（無配件意圖） | 1（`search_products`） |
| 搜尋 + alsoBought 有結果（≥ 3 筆） | 2（search + alsoBought） |
| 搜尋 + alsoBought 無結果 + 類別搜尋 | 3（search + alsoBought + search） |
| 最壞情況 | **3 / 5** ✅ |

---

## 8. Gemini AI 整合

### 個人化 System Instruction 注入

當 `user_context` 存在時，`GeminiClient.build_system_instruction()` 在標準 instruction 末尾附加個人化區塊：

```
══════════════════════════════════════════════════════════════════════
PERSONALIZED CONTEXT (from user's browsing/scan history on their device):
══════════════════════════════════════════════════════════════════════
• Recently explored categories: Televisions, Home Theater
• Preferred brands: Samsung, Sony
• Recently viewed product SKUs: 6537375, 6532276
• Total interactions tracked: 8

Use this context to:
  1. Greet or acknowledge the user's taste naturally
  2. Prioritize results matching their preferred brands
  3. Call get_complementary_products() for the main product found
  4. MOST RECENT SKU = 6537375
     → When accessory intent detected, call get_complementary_products(sku=6537375)
══════════════════════════════════════════════════════════════════════
```

### Multi-Round Function Calling 迴圈

Gemini 可能需要多輪 function call 才能完成回應，`chat_service.py` 實作最多 3 輪的迴圈：

```
Round 0: Gemini → [search_products("Samsung TV")]
  ↓ execute search_products → 返回 TV 結果
Round 1: Gemini → [get_complementary_products("6537375")]
  ↓ execute get_complementary_products → 返回 soundbar 結果
Round 2: Gemini → 最終文字回應（列出 TV + soundbar）
```

---

## 9. 完整請求流程圖

```
用戶操作（Android App）
│
├─ 瀏覽/掃描產品
│    └─ trackView() / trackScan() / trackAddToCart()
│         └─ 寫入 Room DB (UserInteraction)
│
└─ 輸入訊息送出
      │
      ▼
  ChatRepository.sendMessage()
      │
      ├─ UserBehaviorRepository.getBehaviorSummary()
      │    └─ 查詢 Room DB → UserBehaviorContext
      │         (若無記錄則 null，略過個人化)
      │
      └─ POST /chat  { message, session_id, user_context }
              │
              ▼
         UCP Server: ChatService.process_message()
              │
              ├─ build_system_instruction(user_context)
              │    → 將 categories/brands/skus 注入 Gemini prompt
              │
              ├─ [if accessory intent + recent_skus exist]
              │    → Proactive Fetch 預先執行
              │    → get_complementary_products(sku, category_hints)
              │         Call 1: alsoBought(sku)        ← BestBuy API
              │         Call 2: search_products(query) ← 僅在結果 < 3 時
              │    → 把商品列表注入 system instruction
              │
              ├─ Gemini 2.5 Flash
              │    ├─ 理解用戶意圖
              │    ├─ 呼叫需要的 function（search_products 等）
              │    ├─ [若未觸發 proactive] 自主呼叫 get_complementary_products
              │    └─ 生成自然語言回應
              │
              └─ Response: { message, products[] }
                    │
                    ▼
              Android ChatActivity
                    ├─ 顯示 AI 訊息泡泡
                    └─ 若 products[] 不為空：
                         顯示 Product Cards (RecyclerView)
                         └─ 可點擊進入 ProductDetailActivity
```

---

## 10. 相關檔案索引

### Android (Kotlin)

| 檔案 | 說明 |
|------|------|
| [data/model/ChatModels.kt](app/src/main/java/com/bestbuy/scanner/data/model/ChatModels.kt) | `UserBehaviorContext` 資料類別定義 |
| [data/dao/UserInteractionDao.kt](app/src/main/java/com/bestbuy/scanner/data/dao/UserInteractionDao.kt) | Room DB 查詢：`getTopManufacturers`、`getRecentSkus`、`getMostViewedCategories` |
| [data/repository/UserBehaviorRepository.kt](app/src/main/java/com/bestbuy/scanner/data/repository/UserBehaviorRepository.kt) | 行為追蹤 + `getBehaviorSummary()` |
| [data/repository/ChatRepository.kt](app/src/main/java/com/bestbuy/scanner/data/repository/ChatRepository.kt) | 在 `sendMessage()` 中附加 `userContext` |
| [ui/viewmodel/RecommendationViewModel.kt](app/src/main/java/com/bestbuy/scanner/ui/viewmodel/RecommendationViewModel.kt) | `trackView()` / `trackScan()` / `trackAddToCart()` |
| [ui/adapter/ChatAdapter.kt](app/src/main/java/com/bestbuy/scanner/ui/adapter/ChatAdapter.kt) | 在 AI 訊息下方渲染 Product Cards (`productsRecyclerView`) |

### UCP Server (Python)

| 檔案 | 說明 |
|------|------|
| [app/schemas/chat.py](ucp_server/app/schemas/chat.py) | `UserBehaviorContext` Pydantic schema、`ChatRequest.user_context` |
| [app/services/chat_service.py](ucp_server/app/services/chat_service.py) | `process_message()`、`_is_accessory_intent()`、Proactive Fetch 邏輯 |
| [app/services/bestbuy_client.py](ucp_server/app/services/bestbuy_client.py) | `get_complementary_products()`、`CATEGORY_NAME_TO_QUERIES`、`_get_complement_query()` |
| [app/services/gemini_client.py](ucp_server/app/services/gemini_client.py) | `build_system_instruction()`、`get_complementary_products` function declaration |
| [app/services/rate_limiter.py](ucp_server/app/services/rate_limiter.py) | 5 req/min 滑動視窗 RateLimiter |
| [app/api/chat.py](ucp_server/app/api/chat.py) | `/chat` endpoint，傳遞 `user_context` 給 `process_message()` |
