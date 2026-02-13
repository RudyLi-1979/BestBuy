# API Rate Limiting Guide

## Best Buy API 限制

| 限制類型 | 數值 | 說明 |
|---------|------|------|
| **每秒請求數** | 5 requests/second | 短期限制 |
| **每日請求數** | 50,000 requests/day | 長期限制 |

## RateLimiter 實現

UCP Server 自動在所有 Best Buy API 調用中應用速率限制：

```python
class BestBuyAPIClient:
    def __init__(self):
        # 自動初始化 RateLimiter (5 req/s, 50k req/day)
        self.rate_limiter = RateLimiter(
            requests_per_second=5,
            requests_per_day=50000
        )
    
    async def search_products(self, query):
        # 每個 API 方法開始時自動等待速率限制
        await self.rate_limiter.acquire()
        # ... 進行 API 調用
```

### 工作原理

1. **Token Bucket 算法**: 使用滑動窗口追蹤最近 1 秒內的請求
2. **自動等待**: 如果達到限制，自動 sleep 直到可以進行下一個請求
3. **每日追蹤**: 追蹤 24 小時內的總請求數

## 測試時的注意事項

### ✅ 良好實踐

```python
# 1. RateLimiter 自動處理（無需手動等待）
client = BestBuyAPIClient()
result1 = await client.search_products("iPhone")  # RateLimiter 自動應用
result2 = await client.search_products("MacBook") # RateLimiter 自動應用

# 2. 在測試之間添加額外延遲（推薦）
await asyncio.sleep(0.3)  # 在不同類型的測試之間

# 3. 減少測試中的 page_size
result = await client.search_products("laptop", page_size=2)  # 而非 10
```

### ❌ 應避免

```python
# ❌ 不要繞過 RateLimiter
# 錯誤：直接使用 httpx 而不是 BestBuyAPIClient
async with httpx.AsyncClient() as client:
    response = await client.get("https://api.bestbuy.com/...")

# ❌ 不要在循環中快速調用多次
for i in range(10):
    await client.search_products(f"product{i}")  # RateLimiter 會處理，但測試會變慢

# ❌ 不要使用過大的 page_size
result = await client.search_products("laptop", page_size=100)  # 浪費 quota
```

## 測試腳本的速率限制

所有測試腳本都已更新以尊重速率限制：

### 1. `test_rate_limiter.py`
**用途**: 驗證 RateLimiter 正確強制執行 5 req/s 限制

```bash
python test_rate_limiter.py
```

**預期輸出**:
- 10 個請求應在 ~2.0 秒內完成
- 任何 1 秒窗口內最多 5 個請求

### 2. `test_categories.py`
**更新**: 在每個測試之間添加 0.3 秒延遲

```bash
python test_categories.py
```

**API 調用**: 5 次
- 4 次 `search_categories`
- 1 次 `advanced_search`

**預計時間**: ~2 秒（有延遲）

### 3. `test_categories_simple.py`
**更新**: 在 API 調用之間添加 0.3 秒延遲

```bash
python test_categories_simple.py
```

**API 調用**: 2 次
**預計時間**: ~0.5 秒

### 4. `test_gemini_categories.py`
**更新**: 查詢之間間隔 1.0 秒

```bash
python test_gemini_categories.py
```

**API 調用**: 取決於 Gemini 的 function calls（通常 3-6 次）
**預計時間**: ~3-5 秒

## 監控 API 使用量

### 檢查 RateLimiter 統計

```python
client = BestBuyAPIClient()
stats = client.rate_limiter.get_stats()

print(stats)
# {
#     'requests_last_second': 3,
#     'requests_per_second_limit': 5,
#     'requests_today': 127,
#     'requests_per_day_limit': 50000,
#     'daily_reset_in_seconds': 82341.2
# }
```

### 日誌輸出

RateLimiter 會自動記錄：

```
INFO     Rate limiter initialized: 5 req/s, 50000 req/day
DEBUG    Request allowed. Recent: 3/5, Daily: 127/50000
DEBUG    Rate limit: 5/5 requests in last second. Waiting 0.234s
WARNING  Daily limit reached (50000 requests). Waiting 1234.5s until reset
```

## 錯誤處理

### HTTP 403 Over Quota

如果看到此錯誤：

```
HTTP error: Client error '403 Over Quota'
```

**原因**: 超過每日 50,000 請求限制

**解決方案**:
1. 等待每日重置（UTC 午夜）
2. 檢查是否有其他服務使用相同 API key
3. 考慮減少測試頻率或優化 API 調用

### HTTP 429 Too Many Requests

如果看到此錯誤：

```
HTTP error: Client error '429 Too Many Requests'
```

**原因**: 超過每秒 5 次請求限制（RateLimiter 失效或被繞過）

**解決方案**:
1. 確保使用 `BestBuyAPIClient` 而非直接 API 調用
2. 檢查是否有多個客戶端實例同時運行
3. 增加測試之間的延遲

## 優化 API 使用

### 1. 使用按需加載

```python
# ❌ 舊方式：每次搜尋都獲取門市資訊（5+ API 調用）
products = await client.search_products("iPhone")
for product in products:
    stores = await client.get_store_availability(product.sku, "94103")

# ✅ 新方式：只在使用者請求時獲取門市資訊
products = await client.search_products("iPhone", page_size=2)
# 只有當使用者明確要求時才：
stores = await client.get_store_availability(selected_sku, zip_code)
```

### 2. 減少預設結果數

```python
# ❌ 舊設定：預設 10 個結果
DEFAULT_PAGE_SIZE = 10  # 1 次搜尋 = 1 API 調用

# ✅ 新設定：預設 2 個結果
DEFAULT_PAGE_SIZE = 2   # 節省 API quota，更快回應
```
### 4. 正確使用萬用字元

```python
# ✅ 正確：只使用結尾萬用字元
result = await client.search_categories(name="Laptop*")
result = await client.search_categories(name="Phone*")

# ❌ 錯誤：Best Buy API 不支援前導或兩邊萬用字元 (返回 400)
result = await client.search_categories(name="*Phone*")
result = await client.search_categories(name="*Laptop")
```
### 3. 快取常用資料

```python
# 考慮快取分類列表（不常變動）
if not hasattr(self, '_categories_cache'):
    self._categories_cache = await client.get_categories()
```

## 開發與生產環境

### 開發環境
- 使用較小的 `page_size` (2-5)
- 在測試之間添加延遲
- 定期檢查 API 使用統計

### 生產環境
- RateLimiter 自動處理所有請求
- 監控每日使用量警報 (例如 40k/50k)
- 實施快取策略減少重複請求

## 測試檢查清單

在運行測試前：

- [ ] 確認 `.env` 中有有效的 `BESTBUY_API_KEY`
- [ ] 檢查今日是否還有 API quota (< 50,000 requests)
- [ ] 測試使用小的 `page_size` 參數
- [ ] 不要同時運行多個測試腳本
- [ ] 觀察日誌確認 RateLimiter 正在工作

---

**更新日期**: 2026-02-13  
**維護者**: UCP Server Team
