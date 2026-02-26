# 推薦系統技術文件

> **最後更新：2026-02-26**  
> 描述 BestBuy Scanner App 的個人化推薦機制，包含配件推薦（Sparky-like）、相關商品推薦，以及搜尋結果後的 **Follow-up Question Chips（推薦問題按鈕）** 完整判斷流程。

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
9. [SKU Detail 預先載入（Pre-fetch）](#9-sku-detail-預先載入pre-fetch)
10. [Follow-up Question Chips（推薦問題按鈕）](#10-follow-up-question-chips推薦問題按鈕)
11. [Best Buy API 欄位擴充](#11-best-buy-api-欄位擴充)
12. [完整請求流程圖](#12-完整請求流程圖)
13. [相關檔案索引](#13-相關檔案索引)

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

## 9. SKU Detail 預先載入（Pre-fetch）

當用戶訊息中明確包含 `SKU: XXXXXXX`（例如點擊 suggestion question chip 後送出），Chat Service 會在呼叫 Gemini 之前立刻預先獲取該 SKU 的完整規格，並注入 `system_instruction`，讓 Gemini 無需再次呼叫 API 就能精準回答尺寸、保固、重量等問題。

### 觸發條件

```python
# chat_service.py — process_message() 中，位於 "Call Gemini" 之前
sku_in_message = re.findall(r'\bSKU[:\s#]+(\d{6,8})\b', message, re.IGNORECASE)
if sku_in_message:
    detail_product = await self.bestbuy_client.get_product_by_sku(detail_sku)
    # 注入完整規格到 system_instruction
```

### 注入格式

```
══════════════════════════════════════════════════════════════════════════
FULL PRODUCT DETAIL for SKU 6578065 (Samsung 77" S90D OLED TV):
  Price: $1759.99 (on sale, was $1999.99)
  Dimensions & Weight:
    Product Width: 67.7 inches
    Product Height With Stand: 41.7 inches
    Product Height Without Stand: 38.6 inches
    Product Depth With Stand: 14.1 inches
    Product Depth Without Stand: 1.8 inches
    Product Weight With Stand: 80.7 pounds
    Product Weight Without Stand: 76.7 pounds
    Stand Width: 14.4 inches
    Stand Depth: 14.1 inches
  Color: Graphite Black
  Customer Rating: 4.1 (935 reviews)
  Warranty (Labor): 1 year
  Warranty (Parts): 1 year
INSTRUCTION: Use ONLY the data above to answer the user's question.
══════════════════════════════════════════════════════════════════════════
```

### 尺寸資料來源：`details[]` 集合

BestBuy API 的標準 `height`/`depth`/`weight` 欄位通常為空，實際尺寸存放在 `details.name`/`details.value` 集合中（含 Stand / Without Stand 分項）。

| 標準欄位（通常空） | details[] 集合（實際資料）|
|---|---|
| `height: null` | `Product Height With Stand: 41.7 inches` |
| `depth: null` | `Product Depth With Stand: 14.1 inches` |
| `weight: null` | `Product Weight With Stand: 80.7 pounds` |
| `width: "67.7 inches"` ✅ | `Product Width: 67.7 inches` |

`get_product_by_sku()` 的 `show=` 參數現已加入 `details.name,details.value`；Pre-fetch 邏輯優先讀取 `details[]`，再 fallback 到標準欄位，合併後全部注入 Gemini context。

---

## 10. Follow-up Question Chips（推薦問題按鈕）

搜尋結果顯示後，Server 在 `suggested_questions` 欄位返回最多 **3 個**可點擊的問題按鈕。由 `chat_service.py` 的 `_generate_suggested_questions()` 依照**真實商品資料**動態生成，不使用 LLM，速度快且確定性高。

### 觸發條件

```python
if display_products:
    suggested_questions = await self._generate_suggested_questions(
        user_message=message,
        products=display_products   # 最多 8 筆推送給前端的商品
    )
```

### 商品類別偵測

```python
_is_audio       = any(w in _all_text for w in ['headphone', 'earphone', 'earbud', 'airpod', 'speaker', ...])
_is_tv_monitor  = any(w in _all_text for w in ['tv', 'television', 'monitor', 'oled', 'qled', ...])
_is_appliance   = any(w in _all_text for w in ['refrigerator', 'washer', 'dryer', 'microwave', ...])
_is_laptop_tablet = any(w in _all_text for w in ['laptop', 'macbook', 'tablet', 'ipad', ...])
_single_product = len(products) == 1
```

> ⚠️ **Important fix**：`_is_audio` **前置於** `_is_tv_monitor` 判斷。耳機商品名稱可能含 `screen` 字樣（如 noise-cancelling + screen），若先判斷 TV 會誤觸發「其他螢幕尺寸」問題。

### 情況 A：單一商品（`_single_product == True`）

適用：掃描條碼、搜尋精確型號、或搜尋結果只剩 1 筆時。

> **設計原則**：Product Card 已顯示 ★ 評分、Sale badge、售價、省多少錢。因此 suggestion questions **不再重複詢問評分或是否折扣**，改為提供卡片上看不到的深度購買決策資訊。

| 優先序 | 問題 | 智能跳過條件 | Gemini 回答方式 |
|--------|------|-------------|----------------|
| SQ1 | **保固說明？** | 用戶剛問過保固相關詞 | 讀取 Pre-fetch 注入的 `warrantyLabor/warrantyParts` |
| SQ2 | **其他顏色/配置？** | 用戶剛問過顏色相關詞 | 若有 `productVariations`：「其他顏色或配置」；否則「是否有其他外觀選項」 |
| SQ3 | **有 Open Box / 翻新品 / 二手品？** | 用戶剛問過 open box/refurb/pre-owned | 觸發 `get_open_box_options(sku)` |
| SQ4 | **尺寸與重量？** | 用戶剛問過 dimension/weight/size 相關詞 | 讀取 Pre-fetch 注入的 `details[]` 尺寸資料 |
| SQ5 | **盒內附件有哪些？** | 用戶剛問過 included/in the box | 讀取 `includedItemList`；若有資料：「What comes in the box」；否則：「What's included」 |
| SQ6 | **推薦配件？** | — | 若有 `accessories` 資料：「compatible accessories」；否則：「recommended accessories」 |
| SQ7 | 目前有特別優惠？ | — | 僅在有明確 `offers` 資料時才加入 pool |

**智能去重機制**：每個問題都有對應的關鍵詞偵測，若用戶剛問過相關問題，自動跳過該問題，顯示 pool 中下一個，不浪費 chip 名額。

```python
_already_asked_dims     = any(kw in user_message.lower() for kw in ['dimension','weight','height','width','depth','size','how big','how heavy'])
_already_asked_warranty = any(kw in user_message.lower() for kw in ['warrant','guarantee','coverage'])
_already_asked_openbox  = any(kw in user_message.lower() for kw in ['open box','refurb','pre-owned','preowned','used','second hand'])
_already_asked_color    = any(kw in user_message.lower() for kw in ['color','colour','finish','variant','configuration'])
_already_asked_included = any(kw in user_message.lower() for kw in ["what's included","in the box","comes with","included"])
```

### 情況 B：多商品結果（`_single_product == False`）

| 優先序 | 問題 | 判斷條件 |
|--------|------|----------|
| MQ1 | 哪款評分最高？ | 固定（多商品時 rating 不在卡片顯示）|
| MQ2 | 哪款折扣最大？ | `best_savings > 0` |
| MQ3 | 類別規格問題（見下表）| 類別偵測 |
| MQ4 | 顏色/外觀選項？ | `len(colors) >= 2` |
| MQ5 | 目前有特別促銷？ | `has_offers` / `has_savings_data` / `on_sale_count > 0` |
| MQ6 | 推薦配件？ | `has_accessories` |
| MQ7 | 哪款目前特價？ | `0 < on_sale_count < len(products)` |
| MQ8 | 價格區間？ | `len(prices) >= 2 and max > min` |
| MQ9 | 免運費選項？ | `free_ship_count > 0` |

**多商品類別規格問題（Q3）：**

| 偵測類別（依判斷優先序）| 問題文字 |
|------------------------|----------|
| `_is_audio` ← **最優先** | Are there wired or wireless variants? |
| `_is_tv_monitor` | Are there other screen size options? |
| `_is_appliance` | Are there other capacity or size options? |
| `_is_laptop_tablet` | Are there other screen size or storage configurations? |
| 其餘 | Are there other configurations or sizes? |

### Open Box API 整合

當 Gemini 回應「有翻新品/Open Box？」chip 時呼叫：

```
GET /beta/products/{sku}/openBox
```

Server 封裝回傳：

```json
{
  "success": true,
  "has_open_box": true,
  "sku": "6428324",
  "product_name": "Apple iPhone 15 Pro",
  "new_price": 999.99,
  "offers": [
    { "condition": "excellent", "open_box_price": 849.99, "regular_price": 999.99 },
    { "condition": "certified",  "open_box_price": 899.99, "regular_price": 999.99 }
  ]
}
```

- **excellent**：外觀如新，含所有原廠配件，無刮痕
- **certified**：通過 Geek Squad 認證流程

---

## 11. Best Buy API 欄位擴充

### 搜尋端點（search_by_upc、search_products、advanced_product_search）新增欄位

| 欄位 | 說明 | 用途 |
|------|------|------|
| `color` | 商品顏色字串（如 `"Black"`） | Q3/Q4 顏色 chip 判斷 |
| `condition` | `"new"` / `"refurbished"` / `"pre-owned"` | 翻新品偵測 |
| `preowned` | boolean | 二手商品標記 |
| `dollarSavings` | 省幾元（float） | Q2 折扣 chip、Gemini 報價 |
| `percentSavings` | 省幾% （字串） | Gemini 回答省幾% |

### Detail 端點（get_product_by_sku）額外欄位

| 欄位 | 說明 | 用途 |
|------|------|------|
| `warrantyLabor` | 人工保固（如 `"1 Year"`） | SQ1 保固 chip、Pre-fetch 注入 |
| `warrantyParts` | 零件保固 | SQ1 保固 chip、Pre-fetch 注入 |
| `productVariations.sku` | 同款其他顏色/配置 SKU 列表 | SQ2 顏色/版本 chip |
| `features.feature` | 商品功能特色清單 | Gemini 功能問答 |
| `includedItemList.includedItem` | 盒內附件清單 | SQ5 盒內附件 chip |
| `accessories.sku/.name` | 相容配件 | SQ6 配件 chip |
| `offers.id/.text/.type/.startDate/.endDate/.url` | 促銷資訊 | SQ7 優惠 chip |
| `details.name` | 規格項目名稱（如 `"Product Height With Stand"`） | Pre-fetch 尺寸注入（SQ4）|
| `details.value` | 規格項目數值（如 `"41.7 inches"`） | Pre-fetch 尺寸注入（SQ4）|

> ⚠️ Nested 欄位（含 `.` 的欄位）**只能加入 detail endpoint** 的 `show=`，搜尋端點加入會導致 **HTTP 400**。  
> ✅ 例外：`details.name,details.value` 在 filter-style URL（`/v1/products(sku=X)`）可正常使用。

### Pydantic Schema（`schemas/product.py`）對應欄位

```python
color: Optional[str] = None
condition: Optional[str] = None                              # "new" | "refurbished" | "pre-owned"
preowned: Optional[bool] = None
dollar_savings: Optional[float] = Field(None, alias="dollarSavings")
percent_savings: Optional[str] = Field(None, alias="percentSavings")
offers: Optional[List[dict]] = None                          # {id, text, type, startDate, endDate, url}
warranty_labor: Optional[str] = Field(None, alias="warrantyLabor")
warranty_parts: Optional[str] = Field(None, alias="warrantyParts")
product_variations: Optional[List[dict]] = Field(None, alias="productVariations")   # [{sku}]
features: Optional[List[dict]] = None                        # [{feature: "..."}]
included_items: Optional[List[dict]] = Field(None, alias="includedItemList")        # [{includedItem: "..."}]
details: Optional[List[dict]] = None                         # [{name: "Product Height With Stand", value: "41.7 inches"}, ...]
```

### Gemini `thinkingBudget: 0` 必要設定

Gemini 2.5 Flash 預設開啟 chain-of-thought，會使 function calling 回應返回空白 message 與 0 products。**所有** Gemini API payload 必須加入：

```python
"generationConfig": {
    "thinkingConfig": {
        "thinkingBudget": 0   # 關閉 chain-of-thought → 穩定 function calling，加快回應速度
    }
}
```

---

## 12. 完整請求流程圖

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
              ├─ [if message contains "SKU: XXXXXXX"]  ← NEW
              │    → SKU Detail Pre-fetch
              │    → get_product_by_sku(sku)
              │         show=...details.name,details.value,...
              │    → 解析 details[] → 尺寸/保固/顏色
              │    → 注入 FULL PRODUCT DETAIL 到 system_instruction
              │
              ├─ Gemini 2.5 Flash
              │    ├─ 理解用戶意圖
              │    ├─ 呼叫需要的 function（search_products 等）
              │    ├─ [若未觸發 proactive] 自主呼叫 get_complementary_products
              │    └─ 生成自然語言回應（可直接引用 Pre-fetch 注入的規格）
              │
              └─ Response: { message, products[], suggested_questions[] }
                    │
                    ▼
              Android ChatActivity
                    ├─ 顯示 AI 訊息泡泡
                    ├─ 若 products[] 不為空：
                    │    顯示 Product Cards (RecyclerView)
                    │    └─ Card 已包含：★ 評分、Sale badge、售價、省多少錢
                    └─ 若 suggested_questions[] 不為空：
                         顯示 3 個 Question Chip 按鈕
                         （單一 SKU：保固→顏色→翻新品→尺寸→盒內→配件）
                         （多商品：評分→折扣→規格→顏色→促銷→配件）
```

---

## 13. 相關檔案索引

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
| [app/schemas/product.py](ucp_server/app/schemas/product.py) | `Product` schema — 含 `color`、`preowned`、`warrantyLabor/Parts`、`productVariations`、`features`、`includedItemList`、**`details`**（規格集合）等欄位定義 |
| [app/services/chat_service.py](ucp_server/app/services/chat_service.py) | `process_message()`（含 **SKU Detail Pre-fetch** 邏輯）、`_is_accessory_intent()`、`_generate_suggested_questions()`（**單商品：保固優先、移除 rating/折扣重複問題、智能去重**；多商品：評分優先）、Proactive Fetch 邏輯 |
| [app/services/bestbuy_client.py](ucp_server/app/services/bestbuy_client.py) | `get_complementary_products()`、`get_open_box_options()`、`_filter_and_rank_results()`、各端點擴充 `show=` 欄位（`color`、`preowned`、`dollarSavings` 等）；`get_product_by_sku()` 新增 **`details.name,details.value`** 取得完整規格 |
| [app/services/gemini_client.py](ucp_server/app/services/gemini_client.py) | `build_system_instruction()`、`get_complementary_products` function declaration、ANSWER FROM EXISTING CONTEXT 新增 `color/variations`/`included_items`/`warranty`/`features` 規則 |
| [app/services/rate_limiter.py](ucp_server/app/services/rate_limiter.py) | 5 req/min 滑動視窗 RateLimiter |
| [app/api/chat.py](ucp_server/app/api/chat.py) | `/chat` endpoint，傳遞 `user_context` 給 `process_message()` |
