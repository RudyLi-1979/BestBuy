# 安全性指南

## API Key 管理

### ✅ 正確做法

本專案使用 `.env` 檔案來管理敏感資訊（如 API Key）：

1. **使用 .env 檔案**
   ```bash
   # .env
   BESTBUY_API_KEY=你的實際API_KEY
   ```

2. **.env 已加入 .gitignore**
   - `.env` 檔案不會被提交到版本控制
   - 只有 `.env.example` 會被提交作為範本

3. **Gradle 讀取 .env**
   - `app/build.gradle.kts` 會自動讀取 `.env` 檔案
   - API Key 會被注入到 `BuildConfig.BESTBUY_API_KEY`

### ❌ 不要這樣做

1. **不要直接寫在程式碼中**
   ```kotlin
   // ❌ 錯誤示範
   val apiKey = "YourActualApiKey123456"
   ```

2. **不要提交 .env 到版本控制**
   - 確認 `.gitignore` 包含 `.env`
   - 提交前檢查：`git status`

3. **不要在公開場合分享**
   - 不要在 Issue、PR、或論壇中貼上 API Key
   - 截圖時注意遮蔽 API Key

## 設定步驟

### 1. 建立 .env 檔案

```bash
# 複製範例檔案
cp .env.example .env

# 編輯 .env 檔案
# 將 YOUR_API_KEY_HERE 替換為實際的 API Key
```

### 2. 驗證設定

建置專案時，Gradle 會讀取 `.env` 並注入到 BuildConfig：

```kotlin
// 在程式碼中使用
val apiKey = BuildConfig.BESTBUY_API_KEY
```

### 3. 團隊協作

當其他開發者 clone 專案時：

1. 他們需要自己建立 `.env` 檔案
2. 參考 `.env.example` 的格式
3. 填入自己的 API Key

## .env 檔案格式

```bash
# 單行註解使用 #
# 格式：KEY=VALUE

# BestBuy API Key
BESTBUY_API_KEY=你的API_KEY

# 其他環境變數（如果未來需要）
# API_BASE_URL=https://api.bestbuy.com/
# DEBUG_MODE=true
```

## 常見問題

### Q: .env 檔案在哪裡？
A: 在專案根目錄（與 `build.gradle.kts` 同層）

### Q: 如何確認 .env 不會被提交？
A: 執行 `git status`，確認 `.env` 不在待提交清單中

### Q: 團隊成員需要我的 API Key 嗎？
A: 不需要。每個開發者應該使用自己的 API Key

### Q: API Key 洩漏怎麼辦？
A: 
1. 立即到 [BestBuy Developer Portal](https://developer.bestbuy.com/) 撤銷 API Key
2. 生成新的 API Key
3. 更新 `.env` 檔案

## CI/CD 環境

如果使用 CI/CD（如 GitHub Actions），需要在 CI 環境中設定環境變數：

### GitHub Actions 範例

```yaml
# .github/workflows/build.yml
env:
  BESTBUY_API_KEY: ${{ secrets.BESTBUY_API_KEY }}
```

在 GitHub Repository Settings → Secrets 中設定 `BESTBUY_API_KEY`。

## 進階安全措施

### 1. ProGuard/R8 混淆

在 Release 建置時，API Key 會被混淆：

```kotlin
// proguard-rules.pro
-keep class com.bestbuy.scanner.BuildConfig { *; }
```

### 2. 代理伺服器

更安全的做法是透過自己的後端伺服器代理 API 請求：

```
Mobile App → Your Backend → BestBuy API
```

這樣 API Key 只存在於後端，不會暴露在 APK 中。

### 3. API Key 限制

在 BestBuy Developer Portal 中設定 API Key 限制：
- IP 白名單
- 請求頻率限制
- 使用量監控

## 檢查清單

上線前檢查：

- [ ] ✅ `.env` 在 `.gitignore` 中
- [ ] ✅ 沒有硬編碼 API Key
- [ ] ✅ `.env.example` 不包含實際 API Key
- [ ] ✅ README 說明如何設定 `.env`
- [ ] ✅ API Key 有設定使用限制
- [ ] ✅ 定期更換 API Key

## 相關連結

- [BestBuy API 安全最佳實踐](https://bestbuyapis.github.io/api-documentation/)
- [Android 安全性指南](https://developer.android.com/topic/security/best-practices)
- [OWASP Mobile Security](https://owasp.org/www-project-mobile-security/)

---

**記住**: 安全性是一個持續的過程，而不是一次性的任務。定期審查和更新安全措施。
