# BestBuy Scanner - 快速設定指南

## 步驟 1: 設定 API Key

1. 在專案根目錄找到 `.env` 檔案（如果沒有，請複製 `.env.example` 並重新命名為 `.env`）
2. 打開 `.env` 檔案
3. 將 `YOUR_API_KEY_HERE` 替換為你的 BestBuy API Key

```bash
# .env
BESTBUY_API_KEY=你的實際API_KEY
```

**重要**: `.env` 檔案已加入 `.gitignore`，不會被提交到版本控制，確保你的 API Key 安全。

## 步驟 2: 同步 Gradle

在 Android Studio 中點擊「Sync Now」或執行：
```bash
./gradlew build
```

## 步驟 3: 執行應用程式

1. 連接 Android 裝置（建議使用實體裝置測試相機功能）
2. 點擊 Run 按鈕（綠色三角形）
3. 授予相機權限

## 測試建議

### 測試用的 UPC 碼

你可以使用以下 UPC 碼進行測試（這些是常見的 BestBuy 產品）：

- **Apple AirPods**: `190199246850`
- **Samsung Galaxy**: `887276311111`  
- **Sony PlayStation**: `711719534464`

### 手動輸入測試

如果沒有實體產品可掃描：
1. 點擊「手動輸入 UPC」按鈕
2. 輸入上述任一 UPC 碼
3. 查看產品詳情和推薦商品

## 疑難排解

### Gradle 同步失敗
- 確認網路連線正常
- 檢查 Android Studio 版本（建議 2021.3 或更新）
- 執行 `./gradlew clean build`

### 相機無法啟動
- 使用實體裝置而非模擬器
- 確認已授予相機權限
- 檢查 AndroidManifest.xml 中的權限設定

### API 請求失敗
- 確認 API Key 正確設定
- 檢查裝置的網路連線
- 查看 Logcat 的錯誤訊息

## 開發環境需求

- Android Studio Arctic Fox (2020.3.1) 或更新版本
- JDK 8 或更新版本
- Android SDK API Level 24 或以上
- Gradle 7.0 或更新版本

## 下一步

應用程式啟動後，你可以：
1. 掃描任何產品的條碼
2. 查看產品詳細資訊
3. 瀏覽推薦商品
4. 點擊商品連結到 BestBuy 官網

祝使用愉快！
