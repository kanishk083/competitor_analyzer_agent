"""
Central Configuration Management
Loads settings from environment variables with validation.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # ===========================================
    # LLM Configuration (GROQ - Llama 3.3)
    # ===========================================
    groq_api_key: str = Field(default="", env="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", env="GROQ_MODEL")
    
    # ===========================================
    # Firecrawl API (Alternative scraping)
    # ===========================================
    firecrawl_api_key: str = Field(default="", env="FIRECRAWL_API_KEY")
    
    # ===========================================
    # Slack Alerts (Optional)
    # ===========================================
    slack_webhook_url: Optional[str] = Field(default=None, env="SLACK_WEBHOOK_URL")
    
    # ===========================================
    # Application Settings
    # ===========================================
    database_path: str = Field(default="./data/competitor_monitor.db", env="DATABASE_PATH")
    webhook_secret: str = Field(default="", env="WEBHOOK_SECRET")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # ===========================================
    # changedetection.io Settings
    # ===========================================
    changedetection_url: str = Field(default="http://localhost:5000", env="CHANGEDETECTION_URL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    def get_db_path(self) -> Path:
        """Get database path and ensure directory exists."""
        db_path = Path(self.database_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return db_path


# Global settings instance
settings = Settings()
