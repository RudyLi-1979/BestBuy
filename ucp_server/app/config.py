"""
Configuration settings for UCP Server
Loads environment variables from .env file
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Best Buy API
    bestbuy_api_key: str
    bestbuy_api_base_url: str = "https://api.bestbuy.com"
    
    # Gemini LLM
    gemini_api_key: str
    gemini_api_url: str
    
    # UCP Server
    ucp_server_host: str = "0.0.0.0"
    ucp_server_port: int = 8000
    ucp_base_url: str
    
    # Database
    database_url: str
    
    # Redis
    redis_url: str
    
    # Security
    secret_key: str
    ucp_private_key_path: str = "./keys/ucp_private.pem"
    ucp_public_key_path: str = "./keys/ucp_public.pem"
    
    # Development
    debug: bool = False
    log_level: str = "DEBUG"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
