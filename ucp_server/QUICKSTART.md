# UCP Server 快速啟動指南

本指南將幫助您快速啟動 UCP Server 的基礎架構。

## 步驟 1：建立虛擬環境並安裝依賴

```powershell
# 進入 ucp_server 目錄
cd ucp_server

# 建立虛擬環境
python -m venv venv

# 啟動虛擬環境
.\venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt
```

## 步驟 2：配置環境變數

```powershell
# 複製環境變數範本
copy .env.example .env

# 編輯 .env 檔案，填入您的 API Keys
# 至少需要填入：
# - BESTBUY_API_KEY
# - GEMINI_API_KEY
```

## 步驟 3：生成 UCP 金鑰對

```powershell
python scripts/generate_keys.py
```

## 步驟 4：初始化資料庫

```powershell
# 資料庫會在首次啟動時自動建立
# 如果需要手動初始化，可以執行：
python -c "from app.database import init_db; init_db()"
```

## 步驟 5：啟動 Server

```powershell
# 開發模式（自動重載）
uvicorn app.main:app --reload --port 8000

# 或使用 Python 直接執行
python -m app.main
```

## 步驟 6：驗證安裝

開啟瀏覽器訪問：

- **API 文件**: http://localhost:8000/docs
- **UCP Profile**: http://localhost:8000/.well-known/ucp
- **Health Check**: http://localhost:8000/health

## 下一步

目前已完成的模組：
- ✅ 專案結構
- ✅ 資料模型（Cart, Order, CheckoutSession）
- ✅ Best Buy API Client
- ✅ 業務邏輯服務（Cart, Checkout, Order）
- ✅ UCP Profile 端點

待實作的模組：
- [ ] Cart API 端點
- [ ] Products API 端點
- [ ] Checkout API 端點
- [ ] Orders API 端點
- [ ] Gemini LLM 整合
- [ ] Android App Chat Mode

請參考 `UCP_Implementation_Plan.md` 了解完整實作計畫。
