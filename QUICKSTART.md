# BestBuy Scanner - 快速設定指南

本專案包含 **Android App** 和 **UCP Server** 兩個部分。

## 第一部分：Android App 設定

### 步驟 1: 設定 API Key

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
3. 授予相機和麥克風權限

---

## 第二部分：UCP Server 設定（可選）

> **注意**: 如果只想測試條碼掃描功能，可以跳過此部分。Chat Mode 需要 UCP Server 才能運作。

### 方法 1: 使用 Docker（推薦）

**前置需求**: Docker Desktop 已安裝並運行

```bash
cd ucp_server

# 配置環境變數
copy .env.example .env
# 編輯 .env 填入 API Keys

# 啟動服務（使用快速腳本）
.\start_docker.ps1

# 或手動啟動
docker-compose up -d

# 查看運行狀態
docker-compose ps

# 查看日誌
docker-compose logs -f
```

Server 將在 `http://localhost:58000` 啟動。

**停止服務**:
```bash
# 使用快速腳本
.\stop_docker.ps1

# 或手動停止
docker-compose down
```

### 方法 2: 本地開發模式

### 方法 2: 本地開發模式

**前置需求**: Python 3.11+

```bash
cd ucp_server

# 建立虛擬環境
python -m venv venv

# 啟動虛擬環境 (Windows)
.\venv\Scripts\activate

# 啟動虛擬環境 (Linux/Mac)
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt
```

### 步驟 2: 配置環境變數

```bash
# 複製環境變數範本
copy .env.example .env

# 編輯 .env 填入 API Keys
```

編輯 `ucp_server/.env`：
```bash
BESTBUY_API_KEY=你的Best_Buy_API_KEY
GEMINI_API_KEY=你的Gemini_API_KEY
GEMINI_API_URL=https://your-gemini-api-url.com
```

### 步驟 3: 啟動 Server

```bash
# 使用 PowerShell 腳本
.\start_server.ps1

# 或直接使用 uvicorn
uvicorn app.main:app --reload --port 58000
```

Server 將在 `http://localhost:58000` 啟動。

### 步驟 4: 測試 Server

訪問以下 URL 確認 Server 正常運作：
- 首頁: http://localhost:58000
- API 文件: http://localhost:58000/docs
- UCP Profile: http://localhost:58000/.well-known/ucp

---

## 測試建議

### 測試 Chat Mode

1. 打開應用程式（自動進入 Chat Mode）
2. 輸入文字或使用語音：
   - 「我想買 iPhone 15 Pro」
   - 「Show me MacBook Pro 14 inch」
   - 「哪裡可以買到 Mac mini?」
3. 查看 AI 回覆和產品卡片
4. 點擊產品卡片查看詳細資訊

### 測試條碼掃描

1. 在 Chat Mode 點擊「📷 Scan」按鈕
2. 授予相機權限
3. 掃描以下測試 UPC 碼：

**測試用的 UPC 碼**

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
