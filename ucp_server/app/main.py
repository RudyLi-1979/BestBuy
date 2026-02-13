"""
FastAPI Main Application
UCP Server entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.api import ucp
import logging

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Best Buy UCP Server",
    description="Universal Commerce Protocol Server integrating Best Buy API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ucp.router, tags=["UCP"])

# Import and include API routers
from app.api import products, cart, checkout, orders, chat

app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(cart.router, prefix="/cart", tags=["Cart"])
app.include_router(checkout.router, prefix="/checkout", tags=["Checkout"])
app.include_router(orders.router, prefix="/orders", tags=["Orders"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting UCP Server...")
    logger.info(f"Environment: {'Development' if settings.debug else 'Production'}")
    logger.info(f"Base URL: {settings.ucp_base_url}")
    
    # Initialize database
    init_db()
    logger.info("Database initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down UCP Server...")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Best Buy UCP Server",
        "version": "0.1.0",
        "status": "running",
        "ucp_profile": f"{settings.ucp_base_url}/.well-known/ucp",
        "docs": f"{settings.ucp_base_url}/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.ucp_server_host,
        port=settings.ucp_server_port,
        reload=settings.debug
    )
