# UCP Server Quick Start Guide

This guide will help you quickly start the basic infrastructure of the UCP Server.

## Step 1: Create a Virtual Environment and Install Dependencies

```powershell
# Enter the ucp_server directory
cd ucp_server

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure Environment Variables

```powershell
# Copy environment variables template
copy .env.example .env

# Edit .env file and fill in your API Keys
# At minimum, you need to fill in:
# - BESTBUY_API_KEY
# - GEMINI_API_KEY
```

## Step 3: Generate UCP Key Pair

```powershell
python scripts/generate_keys.py
```

## Step 4: Initialize Database

```powershell
# Database will be automatically created on first startup
# If you need to manually initialize, you can run:
python -c "from app.database import init_db; init_db()"
```

## Step 5: Start Server

```powershell
# Development mode (auto-reload)
uvicorn app.main:app --reload --port 8000

# Or run directly with Python
python -m app.main
```

## Step 6: Verify Installation

Open a browser and visit:

- **API Documentation**: http://localhost:8000/docs
- **UCP Profile**: http://localhost:8000/.well-known/ucp
- **Health Check**: http://localhost:8000/health

## Next Steps

Completed modules:
- ✅ Project Structure
- ✅ Data Models (Cart, Order, CheckoutSession)
- ✅ Best Buy API Client
- ✅ Business Logic Services (Cart, Checkout, Order)
- ✅ UCP Profile Endpoint

Modules to be implemented:
- [ ] Cart API Endpoints
- [ ] Products API Endpoints
- [ ] Checkout API Endpoints
- [ ] Orders API Endpoints
- [ ] Gemini LLM Integration
- [ ] Android App Chat Mode

Please refer to `UCP_Implementation_Plan.md` for complete implementation plan.
