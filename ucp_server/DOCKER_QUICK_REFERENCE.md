# UCP Server Docker 快速參考

## 🚀 快速啟動

```powershell
cd ucp_server
.\start_docker.ps1
```

## 🛑 停止服務

```powershell
.\stop_docker.ps1
```

## 📋 常用命令

### 容器管理
```powershell
# 啟動服務
docker-compose up -d

# 停止服務
docker-compose stop

# 重啟服務
docker-compose restart

# 停止並移除容器
docker-compose down

# 停止並移除容器及資料卷
docker-compose down -v
```

### 查看狀態
```powershell
# 查看運行狀態
docker-compose ps

# 查看即時日誌
docker-compose logs -f

# 查看最近 100 行日誌
docker-compose logs --tail=100

# 查看資源使用
docker stats bestbuy-ucp-server
```

### 建置與維護
```powershell
# 重建映像
docker-compose build --no-cache

# 重建並啟動
docker-compose up -d --build

# 進入容器
docker-compose exec ucp-server bash
```

### 資料庫操作
```powershell
# 執行遷移
docker-compose exec ucp-server alembic upgrade head

# 回滾遷移
docker-compose exec ucp-server alembic downgrade -1

# 查看遷移歷史
docker-compose exec ucp-server alembic history
```

### 測試
```powershell
# 執行測試
docker-compose exec ucp-server pytest tests/ -v

# 執行特定測試
docker-compose exec ucp-server pytest tests/test_chat.py -v
```

## 🔗 服務地址

- **首頁**: http://localhost:58000
- **API 文件**: http://localhost:58000/docs
- **ReDoc**: http://localhost:58000/redoc
- **UCP Profile**: http://localhost:58000/.well-known/ucp

## 🐛 故障排除

### Docker Desktop 未運行
```powershell
# 從開始菜單啟動 Docker Desktop
```

### 端口被佔用
```powershell
# 查看佔用端口的進程
netstat -ano | findstr :58000

# 停止進程
taskkill /PID <PID> /F
```

### 容器啟動失敗
```powershell
# 查看詳細日誌
docker-compose logs ucp-server

# 重建容器
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 環境變數未載入
```powershell
# 確認 .env 文件存在
ls .env

# 重啟容器
docker-compose restart
```

## 📊 監控

### 查看日誌
```powershell
# 所有服務日誌
docker-compose logs -f

# 只看 UCP Server 日誌
docker-compose logs -f ucp-server

# 顯示時間戳
docker-compose logs -f --timestamps
```

### 資源監控
```powershell
# 實時監控
docker stats

# 只監控 UCP Server
docker stats bestbuy-ucp-server
```

## 🔧 開發技巧

### 熱重載
代碼修改後會自動重載，無需重啟容器。

### 查看容器內文件
```powershell
# 列出容器內文件
docker-compose exec ucp-server ls -la /app

# 查看環境變數
docker-compose exec ucp-server env
```

### 執行 Python 命令
```powershell
# 進入 Python REPL
docker-compose exec ucp-server python

# 執行 Python 腳本
docker-compose exec ucp-server python scripts/generate_keys.py
```

## 🌐 Cloudflare Tunnel

```powershell
# 在另一個終端運行
cloudflared tunnel --url http://localhost:58000
```

這將提供一個公開的 HTTPS URL，可從任何地方訪問。

## 💡 提示

- 使用 `.\start_docker.ps1` 獲得更好的啟動體驗
- 日誌會自動輪轉，不用擔心佔用空間
- 資料庫和金鑰會持久化，刪除容器不會丟失資料
- 修改代碼後無需重啟，會自動重載

---

**快速參考 - 保持這個文件在手邊！** 📌
