# UCP Server Docker 化完成

**日期**: 2026-02-13  
**狀態**: ✅ 完成

## 變更摘要

UCP Server 現已支援 Docker 容器化部署，使用端口 **58000**。

## 新增檔案

### 1. **Dockerfile**
- 基於 Python 3.11-slim
- 自動安裝所有依賴
- 暴露端口 58000
- 包含健康檢查
- 自動創建必要目錄

### 2. **docker-compose.yml**
- 服務名稱: `ucp-server`
- 容器名稱: `bestbuy-ucp-server`
- 端口映射: `58000:58000`
- 自動載入 `.env` 環境變數
- 持久化資料卷:
  - 資料庫 (`ucp_bestbuy.db`)
  - 金鑰目錄 (`keys/`)
- 支援熱重載（開發模式）

### 3. **.dockerignore**
- 排除不必要的檔案
- 減少映像大小
- 提高建置速度

### 4. **start_docker.ps1** (快速啟動腳本)
- 自動檢查 Docker Desktop 狀態
- 自動檢查 .env 文件
- 檢查端口佔用
- 清理舊容器
- 建立並啟動新容器
- 顯示啟動狀態和常用命令

### 5. **stop_docker.ps1** (停止腳本)
- 優雅停止容器
- 可選：移除資料卷
- 顯示當前狀態

## 更新檔案

### 1. **ucp_server/README.md**
- 新增 Docker 快速啟動章節（推薦方式）
- 保留本地開發模式說明
- 新增 Docker 開發指南
- 新增故障排除章節
- 新增 Cloudflare Tunnel 配置說明
- 新增監控與日誌章節

### 2. **根目錄/QUICKSTART.md**
- 更新 UCP Server 設定部分
- 新增方法 1: Docker（推薦）
- 保留方法 2: 本地開發模式
- 統一使用端口 58000

### 3. **根目錄/README.md**
- 更新 UCP Server 安裝說明
- 新增 Docker 安裝步驟
- 統一使用端口 58000

## 使用方式

### 快速啟動（推薦）

```powershell
cd ucp_server

# 1. 配置環境變數
copy .env.example .env
# 編輯 .env 填入 API Keys

# 2. 啟動服務
.\start_docker.ps1

# 3. 訪問服務
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
