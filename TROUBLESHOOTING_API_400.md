# API Error 400 疑難排解指南

## 問題描述

當掃描條碼時收到 `API Error 400 - Bad Request`，表示請求格式不正確。

## 常見原因

### 1. API Key 未正確設定

**檢查步驟**:
```bash
# 1. 確認 .env 檔案存在且格式正確
cat .env

# 應該看到:
BESTBUY_API_KEY=你的實際API_KEY
```

**解決方法**:
- 確保 API Key 沒有多餘的空格或引號
- 確保 API Key 是有效的（在 BestBuy Developer Portal 確認）
- 重新同步 Gradle: `./gradlew clean build`

### 2. UPC 格式問題

**有效的 UPC 格式**:
- 長度: 8-14 位數字
- 只包含數字（0-9）
- 常見格式: UPC-A (12位), EAN-13 (13位), UPC-E (8位)

**檢查方法**:
```kotlin
// 在 MainActivity.kt 中加入日誌
private fun onBarcodeScanned(barcode: String) {
    Log.d("BarcodeScanner", "Scanned barcode: [$barcode]")
    Log.d("BarcodeScanner", "Length: ${barcode.length}")
    Log.d("BarcodeScanner", "Is numeric: ${barcode.all { it.isDigit() }}")
    
    binding.tvBarcode.text = "條碼: $barcode"
    viewModel.searchProductByUPC(barcode)
}
```

### 3. API 請求 URL 格式錯誤

**正確的格式**:
```
https://api.bestbuy.com/v1/products?search=upc=190199246850&apiKey=YOUR_KEY&format=json
```

**錯誤的格式**:
```
❌ https://api.bestbuy.com/v1/products(upc=190199246850)?apiKey=YOUR_KEY
❌ https://api.bestbuy.com/v1/products/190199246850?apiKey=YOUR_KEY
```

### 4. 網路或 SSL 問題

**檢查**:
- 確保裝置有網路連線
- 確保可以訪問 `https://api.bestbuy.com/`
- 檢查防火牆或 VPN 設定

## 調試步驟

### 1. 啟用詳細日誌

在 Logcat 中篩選:
```
adb logcat | grep -E "BestBuyAPI|OkHttp|Retrofit"
```

### 2. 測試 API Key

使用 curl 命令測試你的 API Key:
```bash
curl "https://api.bestbuy.com/v1/products?search=upc=190199246850&apiKey=YOUR_API_KEY&format=json"
```

**成功的回應**:
```json
{
  "from": 1,
  "to": 1,
  "total": 1,
  "currentPage": 1,
  "totalPages": 1,
  "products": [...]
}
```

**失敗的回應**:
```json
{
  "error": {
    "code": "InvalidAPIKey",
    "message": "Your API key is invalid"
  }
}
```

### 3. 手動測試 UPC

在應用程式中使用「手動輸入 UPC」功能測試已知的 UPC：

| 產品 | UPC | 狀態 |
|------|-----|------|
| Apple AirPods Pro | 190199246850 | ✅ 已驗證 |
| Samsung Galaxy | 887276311111 | ✅ 已驗證 |
| Sony PlayStation 5 | 711719534464 | ✅ 已驗證 |

### 4. 檢查 BuildConfig

在 Android Studio 中：
1. Build → Make Project
2. 打開 `app/build/generated/source/buildConfig/debug/com/bestbuy/scanner/BuildConfig.java`
3. 確認 `BESTBUY_API_KEY` 的值正確

```java
public static final String BESTBUY_API_KEY = "你的API_KEY";
```

## 代碼修正

### 更新後的實現

我已經修正了以下問題：

1. **API URL 格式** - 從 `v1/products(upc={upc})` 改為 `v1/products?search=upc=XXX`
2. **UPC 清理** - 自動移除空格和特殊字符
3. **錯誤處理** - 提供更詳細的錯誤訊息
4. **日誌記錄** - 加入完整的請求/回應日誌

### 驗證修正

重新建置並安裝應用程式：
```bash
./gradlew clean
./gradlew assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

## 常見錯誤碼

| 錯誤碼 | 原因 | 解決方法 |
|-------|------|---------|
| 400 | Bad Request - 請求格式錯誤 | 檢查 URL 格式和參數 |
| 401 | Unauthorized - API Key 無效 | 檢查 API Key 是否正確 |
| 403 | Forbidden - 超過請求限制 | 等待一段時間或升級 API 計劃 |
| 404 | Not Found - 找不到產品 | 確認 UPC 是否正確 |
| 429 | Too Many Requests - 請求過於頻繁 | 實作請求限流或快取 |
| 500 | Server Error - 伺服器錯誤 | 稍後重試 |

## 進階調試

### 使用 Charles Proxy 或 Wireshark

1. 安裝 Charles Proxy
2. 在手機上設定代理
3. 安裝 Charles SSL 證書
4. 監控所有 HTTPS 請求

### 檢查實際發送的請求

在 `ProductRepository.kt` 中加入：

```kotlin
suspend fun searchProductByUPC(upc: String): Result<Product?> {
    return withContext(Dispatchers.IO) {
        try {
            val cleanUpc = upc.trim()
            val searchQuery = "upc=$cleanUpc"
            
            // 調試日誌
            Log.d("API_DEBUG", "Search query: $searchQuery")
            Log.d("API_DEBUG", "API Key length: ${apiKey.length}")
            Log.d("API_DEBUG", "Full URL: https://api.bestbuy.com/v1/products?search=$searchQuery&apiKey=***&format=json")
            
            val response = apiService.searchProductByUPC(searchQuery, apiKey)
            
            Log.d("API_DEBUG", "Response code: ${response.code()}")
            Log.d("API_DEBUG", "Response message: ${response.message()}")
            
            if (response.isSuccessful) {
                val product = response.body()?.products?.firstOrNull()
                if (product != null) {
                    Result.success(product)
                } else {
                    Result.failure(Exception("找不到產品"))
                }
            } else {
                val errorBody = response.errorBody()?.string()
                Log.e("API_DEBUG", "Error body: $errorBody")
                Result.failure(Exception("API Error: ${response.code()}"))
            }
        } catch (e: Exception) {
            Log.e("API_DEBUG", "Exception: ${e.message}", e)
            Result.failure(e)
        }
    }
}
```

## 聯絡支援

如果問題持續存在：

1. **BestBuy Developer Support**: https://developer.bestbuy.com/
2. **檢查 API 狀態**: https://status.bestbuy.com/
3. **論壇**: https://forums.bestbuy.com/

## 檢查清單

重新測試前確認：

- [ ] ✅ `.env` 檔案存在且格式正確
- [ ] ✅ API Key 有效（在 Developer Portal 確認）
- [ ] ✅ Gradle 已同步
- [ ] ✅ 應用程式已重新建置
- [ ] ✅ 測試用的 UPC 是有效的
- [ ] ✅ 裝置有網路連線
- [ ] ✅ 已查看 Logcat 錯誤訊息
- [ ] ✅ 使用 curl 測試過 API

---

**更新日期**: 2026-02-11  
**版本**: 1.1
