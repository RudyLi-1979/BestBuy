# API 測試指南

## BestBuy API 端點測試

### 1. 測試產品搜尋 (UPC)

使用以下 curl 命令測試 API：

```bash
curl "https://api.bestbuy.com/v1/products(upc=190199246850)?apiKey=YOUR_API_KEY&format=json"
```

### 2. 測試產品詳情 (SKU)

```bash
curl "https://api.bestbuy.com/v1/products/6443036.json?apiKey=YOUR_API_KEY"
```

### 3. 測試推薦商品

```bash
curl "https://api.bestbuy.com/v1/products/6443036/recommendations.json?apiKey=YOUR_API_KEY"
```

### 4. 測試 Also Viewed

```bash
curl "https://api.bestbuy.com/v1/products/6443036/alsoViewed.json?apiKey=YOUR_API_KEY"
```

## 測試用 UPC 碼

| 產品名稱 | UPC 碼 |
|---------|--------|
| Apple AirPods Pro | 190199246850 |
| Samsung Galaxy | 887276311111 |
| Sony PlayStation 5 | 711719534464 |
| Nintendo Switch | 045496590062 |
| Xbox Series X | 889842640670 |

## 應用程式測試步驟

### 功能測試

1. **條碼掃描測試**
   - 開啟應用程式
   - 授予相機權限
   - 掃描實體產品條碼
   - 驗證產品資訊正確顯示

2. **手動輸入測試**
   - 點擊「手動輸入 UPC」
   - 輸入測試用 UPC（例如：190199246850）
   - 驗證產品資訊載入

3. **產品詳情測試**
   - 檢查產品名稱、圖片顯示
   - 檢查價格資訊（含特價標示）
   - 檢查產品說明
   - 檢查庫存狀態
   - 檢查顧客評價

4. **推薦商品測試**
   - 驗證推薦商品列表顯示
   - 驗證「其他人也看了」列表顯示
   - 點擊推薦商品進入詳情頁
   - 驗證導航功能正常

5. **外部連結測試**
   - 點擊「在 BestBuy 查看」
   - 驗證瀏覽器正確開啟
   - 點擊「加入購物車」
   - 驗證連結正確

### 錯誤處理測試

1. **無網路連線**
   - 關閉網路連線
   - 嘗試掃描條碼
   - 驗證錯誤訊息顯示

2. **無效的 UPC**
   - 輸入無效的 UPC（例如：000000000000）
   - 驗證「未找到產品」訊息

3. **API 限制**
   - 快速連續掃描多個條碼
   - 驗證 API 限制處理

### 效能測試

1. **記憶體使用**
   - 使用 Android Profiler 監控記憶體使用
   - 連續瀏覽多個產品
   - 檢查是否有記憶體洩漏

2. **網路效能**
   - 監控 API 請求時間
   - 檢查圖片載入速度
   - 驗證快取機制

## 常見問題排除

### API 返回 401 錯誤
- 檢查 API Key 是否正確設定
- 確認 API Key 在 BestBuy Developer Portal 中有效

### API 返回 404 錯誤
- 產品可能不存在於 BestBuy 資料庫
- 嘗試其他測試用 UPC

### 推薦商品不顯示
- 並非所有產品都有推薦資料
- 這是正常現象，可嘗試其他產品

### 掃描速度慢
- 確保光線充足
- 保持相機穩定
- 條碼清晰可見

## Logcat 除錯

查看 API 請求的詳細日誌：

```bash
adb logcat | grep -E "BestBuy|OkHttp|Retrofit"
```

## 建議的測試裝置

- **實體裝置**: 建議使用實體裝置測試相機功能
- **最低 API**: Android 7.0 (API 24)
- **建議 API**: Android 10 (API 29) 或更高

## 自動化測試（未來實作）

可以考慮加入：
- Unit Tests (JUnit)
- UI Tests (Espresso)
- Integration Tests
- API Mock Testing
