# 快速修復 API Error 400

## 問題
掃描條碼時收到 `API Error 400`

## 已修正的內容

### 1. **API URL 格式修正** ✅
- **之前**: `v1/products(upc={upc})?apiKey=XXX` ❌
- **現在**: `v1/products?search=upc=XXX&apiKey=YYY` ✅

### 2. **UPC 驗證** ✅
- 自動清理空格和特殊字符
- 驗證 UPC 長度（8-14 位數字）
- 確保只包含數字

### 3. **更好的錯誤處理** ✅
- 詳細的錯誤日誌
- 用戶友好的錯誤訊息
- API 回應內容記錄

## 快速測試

### 步驟 1: 確認 API Key

打開 `.env` 檔案，確認格式正確：
```bash
BESTBUY_API_KEY=你的實際API_KEY
```

**注意**: 不要有引號、空格或其他字符

### 步驟 2: 重新建置

```bash
# Windows PowerShell
.\gradlew clean build
```

或在 Android Studio 中：
- **Build → Clean Project**
- **Build → Rebuild Project**

### 步驟 3: 測試

使用以下測試 UPC（已知有效）：
- `190199246850` - Apple AirPods Pro
- `887276311111` - Samsung Galaxy
- `711719534464` - Sony PlayStation 5

### 步驟 4: 查看日誌

在 Logcat 中篩選：
```
Tag: BestBuyAPI
Tag: MainActivity
Tag: OkHttp
```

你應該看到：
```
D/MainActivity: === Barcode Scanned ===
D/MainActivity: Raw barcode: [190199246850]
D/MainActivity: Length: 12
D/MainActivity: Is numeric: true
D/MainActivity: Starting product search for UPC: 190199246850
```

## 如果還是失敗

### 檢查 API Key 有效性

使用 curl 測試：
```bash
curl "https://api.bestbuy.com/v1/products?search=upc=190199246850&apiKey=你的API_KEY&format=json"
```

**成功的回應** (200 OK):
```json
{
  "from": 1,
  "to": 1,
  "total": 1,
  "products": [
    {
      "sku": 6443036,
      "name": "Apple - AirPods Pro",
      ...
    }
  ]
}
```

**失敗的回應** (400/401):
```json
{
  "error": {
    "code": "InvalidAPIKey",
    "message": "Your API key is invalid or has expired"
  }
}
```

### 常見問題

1. **API Key 錯誤**
   - 到 https://developer.bestbuy.com/ 確認 API Key
   - 檢查是否過期或被撤銷
   - 重新生成新的 API Key

2. **網路問題**
   - 確認裝置有網路連線
   - 嘗試訪問 https://www.bestbuy.com/
   - 檢查防火牆設定

3. **Gradle 同步問題**  
   - 刪除 `.gradle` 資料夾
   - 執行 `.\gradlew clean`
   - 重新同步專案

## 更新的檔案

以下檔案已修正：
- ✅ `BestBuyApiService.kt` - API 端點格式
- ✅ `ProductRepository.kt` - UPC 清理和錯誤處理
- ✅ `MainActivity.kt` - UPC 驗證和日誌
- ✅ `ApiDebugHelper.kt` - 新增調試工具

## 下一步

1. 重新建置應用程式
2. 安裝到裝置
3. 嘗試掃描或手動輸入測試 UPC
4. 查看 Logcat 確認請求格式正確

如果問題持續，請查看完整的故障排除指南：
- [TROUBLESHOOTING_API_400.md](TROUBLESHOOTING_API_400.md)

---

**更新時間**: 2026-02-11 18:40
