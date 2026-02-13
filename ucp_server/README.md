# UCP Server

本地 UCP (Universal Commerce Protocol) Server，整合 Best Buy API，提供 AI 購物對話功能。

## 🐳 Docker 快速啟動（推薦）

### 前置需求

- Docker Desktop（已安裝並運行）
- Best Buy API Key
- Gemini API Key

### 1. 配置環境變數

```bash
# 複製環境變數範本
copy .env.example .env

# 編輯 .env 填入 API Keys
# BESTBUY_API_KEY=你的API_KEY
# GEMINI_API_KEY=你的Gemini_KEY
# GEMINI_API_URL=你的Gemini_URL
```

### 2. 啟動服務

```bash
# 建立並啟動容器
docker-compose up -d

# 查看運行狀態
docker-compose ps

# 查看日誌
docker-compose logs -f
```

Server 將在 `http://localhost:58000` 啟動。

### 3. 停止服務

```bash
# 停止容器
docker-compose stop

# 停止並移除容器
docker-compose down

# 停止並移除容器及資料卷
docker-compose down -v
```

### 常用 Docker 命令

```bash
# 重建映像
docker-compose build --no-cache

# 重啟服務
docker-compose restart

# 進入容器
docker-compose exec ucp-server bash

# 查看容器日誌
docker-compose logs -f ucp-server
```

---

## 💻 本地開發模式（不使用 Docker）

### 1. 安裝依賴

```bash
# 建立虛擬環境
python -m venv venv

# 啟動虛擬環境（Windows）
.\venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt
```

### 2. 配置環境變數

```bash
# 複製環境變數範本
copy .env.example .env

# 編輯 .env 填入 API Keys
```

### 3. 生成 UCP 公私鑰

```bash
python scripts/generate_keys.py
```

### 4. 初始化資料庫

```bash
alembic upgrade head
```

### 5. 啟動 Server

```bash
# 使用 PowerShell 腳本
.\start_server.ps1

# 或直接使用 uvicorn
uvicorn app.main:app --reload --port 58000
```

Server 將在 `http://localhost:58000` 啟動。

## 📚 API 文件

啟動 Server 後，訪問：
- 首頁: `http://localhost:58000`
- Swagger UI: `http://localhost:58000/docs`
- ReDoc: `http://localhost:58000/redoc`
- UCP Profile: `http://localhost:58000/.well-known/ucp`

## 📁 專案結構

```
ucp_server/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 應用程式入口
│   ├── config.py                  # 環境變數配置
│   ├── models/                    # SQLAlchemy 資料模型
│   ├── schemas/                   # Pydantic 資料驗證
│   ├── services/                  # 業務邏輯層
│   ├── api/                       # API 路由
│   ├── database.py                # 資料庫連線
│   └── dependencies.py            # 依賴注入
├── tests/                         # 測試檔案
├── alembic/                       # 資料庫遷移
├── keys/                          # UCP 公私鑰
├── scripts/                       # 工具腳本
├── .env                           # 環境變數（不提交）
├── .env.example                   # 環境變數範本
├── Dockerfile                     # Docker 映像配置
├── docker-compose.yml             # Docker Compose 配置
├── .dockerignore                  # Docker 忽略文件
├── requirements.txt               # Python 依賴
└── README.md                      # 本檔案
```

**使用 Docker:**
```bash
docker-compose exec ucp-server pytest tests/ -v
```

**本地環境:**
```bash
pytest tests/ -v
```

### 資料庫遷移

**使用 Docker:**
```bash
# 建立新的遷移
docker-compose exec ucp-server alembic revision --autogenerate -m "description"

# 執行遷移
docker-compose exec ucp-server alembic upgrade head

# 回滾遷移
docker-compose exec ucp-server alembic downgrade -1
```

**本地環境:**
```bash
# 建立新的遷移
alembic revision --autogenerate -m "description"

# 執行遷移
alembic upgrade head

# 回滾遷移
alembic downgrade -1
```

## 🔧 故障排除

### Docker 相關問題

**問題：容器無法啟動**
```bash
# 檢查容器狀態
docker-compose ps

# 查看詳細日誌
docker-compose logs ucp-server

# 重建容器
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**問題：端口 58000 已被佔用**
```bash
# Windows PowerShell 查看佔用端口的進程
netstat -ano | findstr :58000

# 停止佔用端口的進程（替換 PID）
taskkill /PID <PID> /F

# 或修改 docker-compose.yml 中的端口映射
ports:
  - "58001:58000"  # 使用不同的外部端口
```

**問題：.env 文件未正確載入**
```bash
# 確認 .env 文件在 ucp_server 目錄下
# 確認文件格式正確（無 BOM、UTF-8 編碼）
# 重啟容器
docker-compose restart
```

### API 連接問題

**問題：Android App 無法連接到 Server**
- 確認 Docker 容器正在運行：`docker-compose ps`
- 確認端口映射正確：`http://localhost:58000`
- 如使用 Cloudflare Tunnel，確認隧道正在運行

## 🌐 Cloudflare Tunnel 配置（可選）

如需從外部網路訪問（例如實體 Android 裝置），可使用 Cloudflare Tunnel：

```bash
# 在另一個終端運行
cloudflared tunnel --url http://localhost:58000
```

這將提供一個公開的 HTTPS URL，可從任何地方訪問。

## 📊 監控與日誌

### 查看即時日誌
```bash
# 所有服務
docker-compose logs -f

# 特定服務
docker-compose logs -f ucp-server

# 最近 100 行
docker-compose logs --tail=100 ucp-server
```

### 容器資源使用
```bash
# 查看資源使用情況
docker stats bestbuy-ucp-server

```bash
pytest tests/ -v
```

### 資料庫遷移

```bash
# 建立新的遷移
alembic revision --autogenerate -m "description"

# 執行遷移
alembic upgrade head

# 回滾遷移
alembic downgrade -1
```

## 授權

本專案僅供學習和參考使用。
