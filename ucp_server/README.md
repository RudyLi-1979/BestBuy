# UCP Server

Local UCP (Universal Commerce Protocol) Server, integrating Best Buy API to provide AI shopping conversation features.

## 🐳 Docker Quick Start (Recommended)

### Prerequisites

- Docker Desktop (Installed and running)
- Best Buy API Key
- Gemini API Key

### 1. Configure Environment Variables

```bash
# Copy environment variable template
copy .env.example .env

# Edit .env and fill in API Keys
# BESTBUY_API_KEY=YOUR_API_KEY
# GEMINI_API_KEY=YOUR_GEMINI_KEY
# GEMINI_API_URL=YOUR_GEMINI_URL
```

### 2. Start Services

```bash
# Build and start containers
docker-compose up -d

# Check running status
docker-compose ps

# View logs
docker-compose logs -f
```

Server will start at `http://localhost:58000`.

### 3. Stop Services

```bash
# Stop container
docker-compose stop

# Stop and remove container
docker-compose down

# Stop and remove container and data volume
docker-compose down -v
```

### Common Docker Commands

```bash
# Rebuild image
docker-compose build --no-cache

# Restart service
docker-compose restart

# Enter container
docker-compose exec ucp-server bash

# View container logs
docker-compose logs -f ucp-server
```

---

## 💻 Local Development Mode (Without Docker)

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy environment variable template
copy .env.example .env

# Edit .env to fill in API Keys
```

### 3. Generate UCP Public/Private Keys

```bash
python scripts/generate_keys.py
```

### 4. Initialize Database

```bash
alembic upgrade head
```

### 5. Start Server

```bash
# Using PowerShell script
.\start_server.ps1

# Or directly using uvicorn
uvicorn app.main:app --reload --port 58000
```

Server will start at `http://localhost:58000`.

## 📚 API Documentation

After starting the server, visit:
- Homepage: `http://localhost:58000`
- Swagger UI: `http://localhost:58000/docs`
- ReDoc: `http://localhost:58000/redoc`
- UCP Profile: `http://localhost:58000/.well-known/ucp`

## 📁 Project Structure

```
ucp_server/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   ├── config.py                  # Environment configuration
│   ├── models/                    # SQLAlchemy data models
│   ├── schemas/                   # Pydantic data validation
│   ├── services/                  # Business logic layer
│   ├── api/                       # API routes
│   ├── database.py                # Database connection
│   └── dependencies.py            # Dependency injection
├── tests/                         # Test files
├── alembic/                       # Database migrations
├── keys/                          # UCP public/private keys
├── scripts/                       # Utility scripts
├── .env                           # Environment variables (do not commit)
├── .env.example                   # Environment template
├── Dockerfile                     # Docker image configuration
├── docker-compose.yml             # Docker Compose configuration
├── .dockerignore                  # Docker ignore file
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

**Using Docker:**
```bash
docker-compose exec ucp-server pytest tests/ -v
```

**Local environment:**
```bash
pytest tests/ -v
```

### Database Migrations

**Using Docker:**
```bash
# Create a new migration
docker-compose exec ucp-server alembic revision --autogenerate -m "description"

# Apply migration
docker-compose exec ucp-server alembic upgrade head

# Rollback migration
docker-compose exec ucp-server alembic downgrade -1
```

**Local environment:**
```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Run migrations
alembic upgrade head

# Rollback migrations
alembic downgrade -1
```

## 🔧 Troubleshooting

### Docker-related Issues

**Issue: Container failed to start**
```bash
# Check container status
docker-compose ps

# View detailed logs
docker-compose logs ucp-server

# Rebuild container
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**Issue: Port 58000 is already in use**
```bash
# Check process using port in Windows PowerShell
netstat -ano | findstr :58000

# Kill the process using port (replace PID)
taskkill /PID <PID> /F

# Or modify port mapping in docker-compose.yml
ports:
  - "58001:58000"  # Use a different external port
```

**Issue: .env file not loaded correctly**
```bash
# Confirm .env file is in ucp_server directory
# Confirm file format is correct (no BOM, UTF-8 encoding)
# Restart container
docker-compose restart
```

### API Connection Issues

**Issue: Android App cannot connect to Server**
- Confirm Docker container is running: `docker-compose ps`
- Confirm port mapping is correct: `http://localhost:58000`
- If using Cloudflare Tunnel, confirm tunnel is running

## 🌐 Cloudflare Tunnel Configuration (Optional)

If you need to access from external networks (e.g., physical Android device), you can use Cloudflare Tunnel:

```bash
# Run in another terminal
cloudflared tunnel --url http://localhost:58000
```

This will provide a public HTTPS URL that can be accessed from anywhere.

## 📊 Monitoring and Logging

### View real-time logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f ucp-server

# Last 100 lines
docker-compose logs --tail=100 ucp-server
```

### Container Resource Usage
```bash
# View resource usage
docker stats bestbuy-ucp-server

```bash
pytest tests/ -v
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## License

This project is for learning and reference purposes only.
