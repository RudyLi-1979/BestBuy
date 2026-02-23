# UCP Server Docker Quick Reference

## 🚀 Quick Start

```powershell
cd ucp_server
.\start_docker.ps1
```

## 🛑 Stop Service

```powershell
.\stop_docker.ps1
```

## 📋 Common Commands

### Container Management
```powershell
# Start Service
docker-compose up -d

# Stop Service
docker-compose stop

# Restart Service
docker-compose restart

# Stop and Remove Containers
docker-compose down

# Stop and Remove Containers and Data Volumes
docker-compose down -v
```

### View Status
```powershell
# View Running Status
docker-compose ps

# View Real-time Logs
docker-compose logs -f

# View Last 100 Lines of Logs
docker-compose logs --tail=100

# View Resource Usage
docker stats bestbuy-ucp-server
```

### Build and Maintenance
```powershell
# Rebuild Image
docker-compose build --no-cache

# Rebuild and Start
docker-compose up -d --build

# Enter Container
docker-compose exec ucp-server bash
```

### Database Operations
```powershell
# Run Migration
docker-compose exec ucp-server alembic upgrade head

# Rollback Migration
docker-compose exec ucp-server alembic downgrade -1

# View Migration History
docker-compose exec ucp-server alembic history
```

### Testing
```powershell
# Run Tests
docker-compose exec ucp-server pytest tests/ -v

# Run Specific Tests
docker-compose exec ucp-server pytest tests/test_chat.py -v
```

## 🔗 Service Addresses

- **Home**: http://localhost:58000
- **API Documentation**: http://localhost:58000/docs
- **ReDoc**: http://localhost:58000/redoc
- **UCP Profile**: http://localhost:58000/.well-known/ucp

## 🐛 Troubleshooting

### Docker Desktop Not Running
```powershell
# Start Docker Desktop from the Start Menu
```

### Port Already in Use
```powershell
# View process using the port
netstat -ano | findstr :58000

# Stop the process
taskkill /PID <PID> /F
```

### Container Startup Failed
```powershell
# View detailed logs
docker-compose logs ucp-server

# Rebuild container
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Environment Variables Not Loaded
```powershell
# Verify .env file exists
ls .env

# Restart container
docker-compose restart
```

## 📊 Monitoring

### View Logs
```powershell
# All services logs
docker-compose logs -f

# Only UCP Server logs
docker-compose logs -f ucp-server

# Display timestamps
docker-compose logs -f --timestamps
```

### Resource Monitoring
```powershell
# Real-time monitoring
docker stats

# Monitor only UCP Server
docker stats bestbuy-ucp-server
```

## 🔧 Development Tips

### Hot Reload
Code modifications are automatically reloaded without restarting the container.

### View Files in Container
```powershell
# List files in container
docker-compose exec ucp-server ls -la /app

# View environment variables
docker-compose exec ucp-server env
```

### Execute Python Commands
```powershell
# Enter Python REPL
docker-compose exec ucp-server python

# Execute Python script
docker-compose exec ucp-server python scripts/generate_keys.py
```

## 🌐 Cloudflare Tunnel

```powershell
# Run in another terminal
cloudflared tunnel --url http://localhost:58000
```

This will provide a public HTTPS URL that can be accessed from anywhere.

## 💡 Tips

- Use `.\start_docker.ps1` for a better startup experience
- Logs are automatically rotated, no need to worry about space
- Database and keys are persistent, deleting containers won't lose data
- No need to restart after code changes, automatic reload is enabled

---

**Quick Reference - Keep this file handy!** 📌
