# API 端點測試指南

本文件提供 UCP Server API 端點的測試方法和範例。

## 前置條件

確保 UCP Server 正在運行：
```powershell
cd c:\Users\rudy\AndroidStudioProjects\BestBuy\ucp_server
uvicorn app.main:app --reload --port 8000
```

## API 文件

訪問 Swagger UI 查看完整 API 文件：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 1. Products API 測試

### 1.1 關鍵字搜尋商品

```powershell
# 搜尋 iPhone
curl "http://localhost:8000/products/search?q=iPhone&page_size=5"

# 搜尋並排序
curl "http://localhost:8000/products/search?q=laptop&page_size=10&sort=salePrice.asc"
```

### 1.2 SKU 查詢

```powershell
# 查詢特定商品（需要真實的 SKU）
curl "http://localhost:8000/products/6428324"
```

### 1.3 UPC 查詢

```powershell
# 使用 UPC 條碼查詢
curl "http://localhost:8000/products/upc/195949038488"
```

### 1.4 推薦商品

```powershell
# 獲取推薦商品
curl "http://localhost:8000/products/6428324/recommendations"
```

---

## 2. Cart API 測試

### 2.1 加入商品到購物車

```powershell
curl -X POST "http://localhost:8000/cart/add" `
  -H "Content-Type: application/json" `
  -d '{
    "sku": "6428324",
    "name": "iPhone 15 Pro 128GB",
    "price": 999.99,
    "image_url": "https://example.com/image.jpg",
    "quantity": 1
  }'
```

### 2.2 查看購物車

```powershell
curl "http://localhost:8000/cart"
```

### 2.3 更新商品數量

```powershell
# 更新數量為 2
curl -X PUT "http://localhost:8000/cart/items/6428324" `
  -H "Content-Type: application/json" `
  -d '{"quantity": 2}'

# 設定數量為 0 移除商品
curl -X PUT "http://localhost:8000/cart/items/6428324" `
  -H "Content-Type: application/json" `
  -d '{"quantity": 0}'
```

### 2.4 移除商品

```powershell
curl -X DELETE "http://localhost:8000/cart/items/6428324"
```

### 2.5 清空購物車

```powershell
curl -X DELETE "http://localhost:8000/cart"
```

---

## 3. Checkout API 測試

### 3.1 建立結帳會話

```powershell
# 先加入商品到購物車，然後建立結帳會話
curl -X POST "http://localhost:8000/checkout/session"
```

回應範例：
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "guest_abc123",
  "total_amount": 999.99,
  "created_at": "2026-02-12T10:00:00Z"
}
```

### 3.2 更新配送資訊

```powershell
# 使用上一步獲得的 session_id
curl -X POST "http://localhost:8000/checkout/session/{session_id}/update" `
  -H "Content-Type: application/json" `
  -d '{
    "shipping_name": "John Doe",
    "shipping_address": "123 Main St, Apt 4B",
    "shipping_city": "New York",
    "shipping_postal_code": "10001",
    "shipping_country": "US"
  }'
```

### 3.3 完成結帳

```powershell
# 完成結帳並建立訂單
curl -X POST "http://localhost:8000/checkout/session/{session_id}/complete"
```

回應範例：
```json
{
  "id": 1,
  "order_number": "ORD-20260212-001",
  "total_amount": 999.99,
  "status": "confirmed",
  "items": [...]
}
```

---

## 4. Orders API 測試

### 4.1 查詢所有訂單

```powershell
curl "http://localhost:8000/orders"
```

### 4.2 查詢特定訂單

```powershell
# 使用訂單編號查詢
curl "http://localhost:8000/orders/ORD-20260212-001"
```

### 4.3 更新訂單狀態（管理功能）

```powershell
curl -X PUT "http://localhost:8000/orders/ORD-20260212-001/status?status=shipped"
```

可用狀態：
- `pending` - 待處理
- `confirmed` - 已確認
- `processing` - 處理中
- `shipped` - 已出貨
- `delivered` - 已送達
- `cancelled` - 已取消

---

## 5. UCP Profile 測試

```powershell
curl "http://localhost:8000/.well-known/ucp"
```

---

## 完整購物流程測試

以下是一個完整的購物流程範例：

```powershell
# 1. 搜尋商品
curl "http://localhost:8000/products/search?q=iPhone"

# 2. 加入購物車
curl -X POST "http://localhost:8000/cart/add" `
  -H "Content-Type: application/json" `
  -d '{
    "sku": "6428324",
    "name": "iPhone 15 Pro",
    "price": 999.99,
    "quantity": 1
  }'

# 3. 查看購物車
curl "http://localhost:8000/cart"

# 4. 建立結帳會話
curl -X POST "http://localhost:8000/checkout/session"

# 5. 更新配送資訊（使用上一步的 session_id）
curl -X POST "http://localhost:8000/checkout/session/{session_id}/update" `
  -H "Content-Type: application/json" `
  -d '{
    "shipping_name": "John Doe",
    "shipping_address": "123 Main St",
    "shipping_city": "New York",
    "shipping_postal_code": "10001"
  }'

# 6. 完成結帳
curl -X POST "http://localhost:8000/checkout/session/{session_id}/complete"

# 7. 查詢訂單
curl "http://localhost:8000/orders"
```

---

## 注意事項

1. **Guest User ID**: 目前系統使用簡化的 Guest Checkout，每次請求會自動生成 guest user ID
2. **Best Buy API Key**: 確保 `.env` 檔案中的 `BESTBUY_API_KEY` 已正確設定
3. **真實 SKU/UPC**: 測試時需要使用 Best Buy API 中真實存在的 SKU 或 UPC
4. **Session ID**: 結帳流程中的 `session_id` 需要從建立會話的回應中獲取

---

## 使用 Swagger UI 測試

最簡單的測試方式是使用 Swagger UI：

1. 訪問 http://localhost:8000/docs
2. 展開任一 API 端點
3. 點擊「Try it out」
4. 填入參數
5. 點擊「Execute」
6. 查看回應結果

這樣可以直接在瀏覽器中測試所有 API 端點！
