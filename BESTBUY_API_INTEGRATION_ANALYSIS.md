# Best Buy API 整合分析報告

## 執行摘要

ucp_server 目前**已整合** Best Buy Developer API 的**基礎功能**（約 30% 完整度），包括產品搜尋、UPC/SKU 查詢和簡單推薦。但還有**許多進階功能未實現**，包括門市庫存查詢、產品分類、二手品查詢、熱門商品等。

## 目前實現狀況

### ✅ 已實現 (30%)

| API 類別 | 端點 | 實現方法 | 狀態 |
|---------|------|---------|------|
| Products API | `GET /v1/products(upc={upc})` | `search_by_upc()` | ✅ 完整 |
| Products API | `GET /v1/products/{sku}.json` | `get_product_by_sku()` | ✅ 完整 |
| Products API | `GET /v1/products(search={query})` | `search_products()` | ✅ 完整 + 智能篩選 |
| Recommendations | `GET /v1/products/{sku}/alsoViewed` | `get_recommendations()` | ✅ 完整 |
| Recommendations | `GET /beta/products/{sku}/similar` | `get_similar_products()` | ✅ 完整 |

### ❌ 未實現但重要 (70%)

#### 1. Recommendations API - 進階端點

| 端點 | 用途 | 商業價值 |
|-----|------|---------|
| `/v1/products/{sku}/alsoBought` | 一起購買的商品 | 🔥 高 - 交叉銷售 |
| `/v1/products/{sku}/viewedUltimatelyBought` | 瀏覽後購買的商品 | 🔥 高 - 轉換率優化 |
| `/v1/products/trendingViewed(categoryId={id})` | 熱門商品 (依分類) | 🔥 高 - 吸引流量 |
| `/v1/products/mostViewed(categoryId={id})` | 最多瀏覽 (依分類) | 🔥 高 - 流行趨勢 |

**影響**: 無法提供數據驅動的交叉銷售建議，錯失提升客單價的機會。

#### 2. Stores API - 門市功能

| 端點 | 用途 | 商業價值 |
|-----|------|---------|
| `/v1/stores?area(postalCode,distance)` | 查詢附近門市 | 🔥 高 - 線下引流 |
| `/v1/products/{sku}/stores?postalCode={zip}` | 門市庫存查詢 | 🔥 極高 - 即時庫存 |
| `/v1/stores/{id}?show=services,hours` | 門市服務與營業時間 | 中 - 客戶體驗 |

**影響**: 
- 用戶無法知道附近門市是否有貨
- 無法支持「線上查詢、門市取貨」(BOPIS) 功能
- 錯失 O2O (Online to Offline) 商機

**範例使用場景**:
```
用戶: "附近哪裡能買到 iPhone 15 Pro 256GB？"
目前系統: ❌ 只能告訴線上價格和連結
改進後: ✅ "Richfield 門市 (5.2 英里) 有現貨，可立即取貨"
```

#### 3. Categories API - 分類瀏覽

| 端點 | 用途 | 商業價值 |
|-----|------|---------|
| `/v1/categories` | 所有產品分類 | 中 - 導覽體驗 |
| `/v1/categories(name={name})` | 搜尋分類 | 中 - 輔助搜尋 |
| `/v1/products(categoryPath.id={id})` | 依分類篩選產品 | 🔥 高 - 精準推薦 |

**影響**: 無法實現「瀏覽型購物」體驗，只能靠關鍵字搜尋。

#### 4. Open Box API - 二手優惠

| 端點 | 用途 | 商業價值 |
|-----|------|---------|
| `/beta/products/{sku}/openBox` | 單一產品二手品 | 高 - 價格敏感客群 |
| `/beta/products/openBox(sku in(...))` | 批量查詢二手品 | 高 - 比價功能 |
| `/beta/products/openBox(categoryId={id})` | 分類二手品 | 中 - 清倉優惠 |

**影響**: 
- 無法顯示優惠的展示品/二手品
- 錯失價格敏感客群

**範例**: MacBook Pro 全新 $2499 vs. Open Box Excellent $1999 (-20%)

#### 5. 進階搜尋功能

##### a) 複雜查詢操作符

目前只用 `search`，但官方支持：

```python
# AND 查詢
products(manufacturer=canon&salePrice<1000)
→ Canon 產品且價格低於 $1000

# OR 查詢  
products(wifiReady=true|wifiBuiltIn=true)
→ 有 Wi-Fi 功能的產品

# IN 查詢 (推薦用於多值)
products(sku in(43900,2088495,7150065))
→ 批量查詢特定 SKU

# 日期篩選
products(releaseDate>today)
→ 即將發售的產品

products(releaseDate>=2024-01-01&releaseDate<=2024-12-31)
→ 2024 年發售的產品

# 分類篩選
products(categoryPath.id=abcat0502000&active=true)
→ 筆記型電腦分類且仍在售

# 顏色篩選
products(color in(white,black,silver)&categoryPath.id=abcat0901000)
→ 白色/黑色/銀色的冰箱
```

**建議實現方法**:
```python
async def advanced_search(
    self,
    manufacturer: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    category_id: Optional[str] = None,
    colors: Optional[List[str]] = None,
    release_date_after: Optional[str] = None,
    **kwargs
) -> ProductSearchResponse:
    """
    進階搜尋，支持多條件組合
    """
    filters = []
    
    if manufacturer:
        filters.append(f"manufacturer={manufacturer}")
    
    if price_min:
        filters.append(f"salePrice>={price_min}")
    
    if price_max:
        filters.append(f"salePrice<={price_max}")
    
    if category_id:
        filters.append(f"categoryPath.id={category_id}")
    
    if colors:
        color_filter = " in(" + ",".join(f'"{c}"' for c in colors) + ")"
        filters.append(f"color{color_filter}")
    
    if release_date_after:
        filters.append(f"releaseDate>={release_date_after}")
    
    # 組合所有篩選條件
    filter_string = "&".join(filters)
    url = f"{self.base_url}/v1/products({filter_string})"
    # ... rest of implementation
```

##### b) Facets (彙總資訊)

```python
# 範例：查詢筆電的製造商分布
GET /v1/products(categoryPath.id=abcat0502000)?facet=manufacturer,10

# 回應：
{
  "facets": {
    "manufacturer": {
      "apple": 156,      # Apple 有 156 個產品
      "dell": 142,
      "hp": 138,
      "lenovo": 95,
      "asus": 87
    }
  }
}
```

**使用場景**: 在搜尋結果頁顯示篩選器 (Filter Sidebar)

##### c) Cursor Marks (大量結果分頁)

官方建議：**結果超過 10 頁時必須使用 cursorMark**

```python
# 目前實現 (有問題)：
?page=1&pageSize=100  # OK
?page=50&pageSize=100  # ⚠️ 可能超時或失敗

# 官方推薦 (大量結果)：
?cursorMark=*&pageSize=100  # 第一頁
?cursorMark=AoNeDQ...&pageSize=100  # 第二頁 (使用返回的 nextCursorMark)
```

**建議實現**:
```python
async def search_all_products(
    self,
    query: str,
    batch_size: int = 100
) -> List[Product]:
    """
    使用 cursorMark 獲取所有符合條件的產品
    """
    all_products = []
    cursor_mark = "*"
    
    while cursor_mark:
        url = f"{self.base_url}/v1/products(search={query})"
        params = {
            "apiKey": self.api_key,
            "format": "json",
            "pageSize": batch_size,
            "cursorMark": urllib.parse.quote(cursor_mark)
        }
        
        response = await self.client.get(url, params=params)
        data = response.json()
        
        all_products.extend([Product(**p) for p in data["products"]])
        
        # 獲取下一頁的 cursor
        next_cursor = data.get("nextCursorMark")
        if next_cursor == cursor_mark:  # 沒有更多結果
            break
        cursor_mark = next_cursor
    
    return all_products
```

#### 6. 產品屬性擴展

目前 `show` 參數包含：
```python
"sku,name,regularPrice,salePrice,onSale,image,largeFrontImage,mediumImage,
thumbnailImage,longDescription,shortDescription,manufacturer,modelNumber,
upc,url,addToCartUrl,customerReviewAverage,customerReviewCount,
freeShipping,inStoreAvailability,onlineAvailability"
```

**遺漏的有用屬性**:

| 屬性 | 用途 | 範例值 |
|-----|------|-------|
| `customerTopRated` | 顯示「高評價」標籤 | `true` |
| `features.feature` | 產品特色列表 | `["4K Resolution", "HDR Support"]` |
| `longDescriptionHtml` | HTML 格式描述 (更豐富) | `<p>...</p>` |
| `warrantyLabor` | 人工保固 | `"1 Year Limited Warranty"` |
| `warrantyParts` | 零件保固 | `"90 Days"` |
| `shippingCost` | 運費 | `2.99` |
| `shippingWeight` | 運送重量 | `"2.5 lbs"` |
| `depth`, `height`, `width`, `weight` | 產品尺寸 | 實體產品必要 |
| `digital` | 是否數位產品 | `false` |
| `preowned` | 是否二手 | `false` |
| `condition` | 商品狀況 | `"new"` / `"refurbished"` |
| `categoryPath.name` | 完整分類路徑 | `["Electronics", "Computers", "Laptops"]` |
| `releaseDate` | 發售日期 | `"2024-09-20"` |
| `startDate` | Best Buy 開始販售日期 | `"2024-09-22"` |
| `format` | 媒體格式 | `"Blu-ray"` / `"Digital"` |
| `dollarSavings` | 節省金額 | `200.00` |
| `percentSavings` | 節省百分比 | `20` |
| `onlineAvailabilityUpdateDate` | 庫存更新時間 | `"2024-02-13T10:30:00"` |

**建議方案**:
```python
# 方案 1: 提供不同的預設 show 組合
SHOW_BASIC = "sku,name,salePrice,image"
SHOW_DETAILED = "sku,name,regularPrice,salePrice,onSale,longDescriptionHtml,features.feature,customerReviewAverage,customerReviewCount"
SHOW_FULL = "all"  # 返回所有屬性

# 方案 2: 讓前端指定需要的欄位
async def get_product_by_sku(self, sku: str, show: str = SHOW_DETAILED):
    ...
```

## 優先級建議

### 🔥 高優先級 (立即實現)

1. **門市庫存查詢** (`/products/{sku}/stores`)  
   - **理由**: 核心 O2O 功能，大幅提升用戶體驗
   - **工作量**: 2-4 小時
   - **影響**: 重大商業價值

2. **也一起購買** (`/products/{sku}/alsoBought`)  
   - **理由**: 提升交叉銷售機會
   - **工作量**: 1-2 小時
   - **影響**: 直接影響客單價

3. **進階搜尋操作符**  
   - **理由**: 改善搜尋精確度
   - **工作量**: 4-6 小時
   - **影響**: 用戶體驗大幅提升

### ⚡ 中優先級 (短期規劃)

4. **熱門/流行商品** (`/products/trendingViewed`, `/products/mostViewed`)  
   - **理由**: 引導用戶發現新產品
   - **工作量**: 2-3 小時

5. **Categories API**  
   - **理由**: 支持分類瀏覽
   - **工作量**: 3-5 小時

6. **Facets 彙總**  
   - **理由**: 實現篩選器 UI
   - **工作量**: 4-6 小時

### 🌟 中低優先級 (長期優化)

7. **Open Box API**  
   - **理由**: 吸引價格敏感客群
   - **工作量**: 3-4 小時

8. **Cursor Marks 分頁**  
   - **理由**: 優化大量結果處理
   - **工作量**: 2-3 小時

9. **擴展產品屬性**  
   - **理由**: 更豐富的產品資訊
   - **工作量**: 1-2 小時

## 實現路線圖

### Phase 1: 核心功能增強 (1-2 週)
- [ ] 實現門市庫存查詢
- [ ] 實現 `alsoBought` 推薦
- [ ] 實現進階搜尋操作符 (AND/OR/IN)

### Phase 2: 發現功能 (1 週)
- [ ] 實現熱門商品端點
- [ ] 實現 Categories API
- [ ] 實現 Facets 彙總

### Phase 3: 優化與擴展 (1 週)
- [ ] Open Box API
- [ ] Cursor Marks 分頁
- [ ] 擴展產品屬性

## 技術債務

1. **Schema 不完整**: `Product` model 缺少許多欄位
2. **錯誤處理不足**: 應區分不同 HTTP 錯誤碼 (400, 403, 404, 429, 500)
3. **缺少測試**: 需要單元測試和整合測試
4. **文檔不足**: 缺少 API 使用範例

## 結論

ucp_server 目前的 Best Buy API 整合**僅完成 30% 的官方功能**。雖然基礎搜尋和推薦已實現，但缺少許多高價值功能：

- ❌ 無法查詢門市庫存 (損失 O2O 商機)
- ❌ 推薦功能不完整 (錯失交叉銷售)
- ❌ 搜尋功能過於簡單 (用戶體驗差)
- ❌ 無法顯示二手優惠 (錯失價格敏感客群)

建議優先實現**門市庫存查詢**和**進階搜尋**功能，可在 1-2 週內大幅提升系統競爭力。

## 參考資料

- [Best Buy API 官方文檔](https://bestbuyapis.github.io/api-documentation)
- [Products API](https://bestbuyapis.github.io/api-documentation/#products-api)
- [Recommendations API](https://bestbuyapis.github.io/api-documentation/#recommendations-api)
- [Stores API](https://bestbuyapis.github.io/api-documentation/#stores-api)
- [Search Techniques](https://bestbuyapis.github.io/api-documentation/#search-techniques)
