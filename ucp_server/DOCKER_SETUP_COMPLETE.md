# UCP Server Dockerization Complete

**Date**: 2026-02-13  
**Status**: ✅ Complete

## Change Summary

The UCP Server now supports Docker containerized deployment, using port **58000**.

## New Files

### 1. **Dockerfile**
- Based on Python 3.11-slim
- Automatically installs all dependencies
- Exposes port 58000
- Includes a health check
- Automatically creates necessary directories

### 2. **docker-compose.yml**
- Service name: `ucp-server`
- Container name: `bestbuy-ucp-server`
- Port mapping: `58000:58000`
- Automatically loads `.env` environment variables
- Persistent volumes:
  - Database (`ucp_bestbuy.db`)
  - Keys directory (`keys/`)
- Supports hot-reloading (in development mode)

### 3. **.dockerignore**
- Excludes unnecessary files
- Reduces image size
- Improves build speed

### 4. **start_docker.ps1** (Quick Start Script)
- Automatically checks Docker Desktop status
- Automatically checks for the .env file
- Checks for port conflicts
- Cleans up old containers
- Builds and starts new containers
- Displays startup status and common commands

### 5. **stop_docker.ps1** (Stop Script)
- Gracefully stops containers
- Optional: remove volumes
- Displays the current status

## Updated Files

### 1. **ucp_server/README.md**
- Added Docker Quick Start section (recommended method)
- Kept local development mode instructions
- Added Docker development guide
- Added troubleshooting section
- Added Cloudflare Tunnel configuration instructions
- Added monitoring and logs section

### 2. **根目錄/QUICKSTART.md**
- Updated UCP Server setup section
- Added Method 1: Docker (Recommended)
- Kept Method 2: Local Development Mode
- Standardized on port 58000

### 3. **根目錄/README.md**
- Updated UCP Server installation instructions
- Added Docker installation steps
- Standardized on port 58000

## How to Use

### Quick Start (Recommended)

```powershell
cd ucp_server

# 1. Configure environment variables
copy .env.example .env
# Edit .env and fill in API Keys

# 2. Start the service
.\start_docker.ps1

# 3. Access the service
# http://localhost:58000
```

### 手動啟動

```powershell
cd ucp_server

# 啟動
docker-compose up -d

# 查看狀態
docker-compose ps

# 查看日誌
docker-compose logs -f

# 停止
docker-compose down
```

## 功能特性

### ✅ 開發友好
- **熱重載**: 修改代碼後自動重載，無需重啟容器
- **即時日誌**: `docker-compose logs -f` 查看即時日誌
- **本地掛載**: 代碼掛載到容器，修改立即生效

### ✅ 資料持久化
- **資料庫**: SQLite 資料庫持久化到本地
- **金鑰**: UCP 公私鑰持久化
- **配置**: `.env` 環境變數自動載入

### ✅ 容器管理
- **健康檢查**: 自動監控容器健康狀態
- **自動重啟**: `restart: unless-stopped` 策略
- **網路隔離**: 獨立的 Docker 網路

### ✅ 易用性
- **快速腳本**: PowerShell 腳本一鍵啟動/停止
- **狀態檢查**: 自動檢查 Docker、端口、.env
- **錯誤提示**: 友好的錯誤訊息和解決方案

## 端口說明

- **58000**: UCP Server 主要服務端口
  - 首頁: `http://localhost:58000`
  - API 文件: `http://localhost:58000/docs`
  - UCP Profile: `http://localhost:58000/.well-known/ucp`

## 故障排除

### 問題 1: Docker Desktop 未運行
```powershell
# 解決方案: 啟動 Docker Desktop
# Windows: 從開始菜單啟動 Docker Desktop
```

### 問題 2: 端口 58000 被佔用
```powershell
# 查看佔用端口的進程
netstat -ano | findstr :58000

# 停止進程（替換 PID）
taskkill /PID <PID> /F

# 或修改 docker-compose.yml 使用其他端口
ports:
  - "58001:58000"
```

### 問題 3: 容器無法啟動
```powershell
# 查看詳細日誌
docker-compose logs ucp-server

# 重建容器
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 問題 4: .env 文件未載入
```powershell
# 確認文件位置和格式
# 確保文件在 ucp_server/ 目錄下
# 確保使用 UTF-8 編碼（無 BOM）

# 重啟容器
docker-compose restart
```

## 與 Cloudflare Tunnel 整合

如需從外部網路訪問（實體 Android 裝置）：

```powershell
# 在另一個終端運行
cloudflared tunnel --url http://localhost:58000
```

這將提供一個公開的 HTTPS URL。

## 生產環境建議

如需部署到生產環境，建議：

1. **移除開發掛載**: 
   ```yaml
   # 移除 docker-compose.yml 中的本地掛載
   # volumes:
   #   - .:/app  # 移除此行
   ```

2. **禁用 Reload**:
   ```dockerfile
   # Dockerfile 中移除 --reload
   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "58000"]
   ```

3. **使用環境變數**:
   ```yaml
   # 不使用 .env 文件，直接在 docker-compose.yml 設定
   environment:
     - BESTBUY_API_KEY=${BESTBUY_API_KEY}
   ```

4. **增加資源限制**:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '1'
         memory: 512M
   ```

## 測試確認

啟動後請確認：

1. ✅ 容器正在運行: `docker-compose ps`
2. ✅ 服務可訪問: `http://localhost:58000`
3. ✅ API 文件可訪問: `http://localhost:58000/docs`
4. ✅ Android App 可連接

## 下一步

1. 測試 Chat Mode 功能
2. 驗證所有 API 端點
3. 檢查日誌確認無錯誤
4. 測試與 Android App 的連接

---

**Docker 化完成！** 🐳🎉
