import os
from typing import Optional
from pydantic import BaseSettings, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    
    # Tavily Configuration
    tavily_api_key: str = Field(..., env="TAVILY_API_KEY")
    
    # X (Twitter) Configuration
    x_bearer_token: Optional[str] = Field(None, env="X_BEARER_TOKEN")
    x_api_key: Optional[str] = Field(None, env="X_API_KEY")
    x_api_secret: Optional[str] = Field(None, env="X_API_SECRET")
    x_access_token: Optional[str] = Field(None, env="X_ACCESS_TOKEN")
    x_access_token_secret: Optional[str] = Field(None, env="X_ACCESS_TOKEN_SECRET")
    
    # Reddit Configuration
    reddit_client_id: Optional[str] = Field(None, env="REDDIT_CLIENT_ID")
    reddit_client_secret: Optional[str] = Field(None, env="REDDIT_CLIENT_SECRET")
    reddit_user_agent: str = Field("TechTrendNotifier/1.0", env="REDDIT_USER_AGENT")
    
    # Slack Configuration
    slack_bot_token: str = Field(..., env="SLACK_BOT_TOKEN")
    slack_channel: str = Field(..., env="SLACK_CHANNEL")
    
    # Application Settings
    log_level: str = Field("INFO", env="LOG_LEVEL")
    max_articles_per_source: int = Field(10, env="MAX_ARTICLES_PER_SOURCE")
    similarity_threshold: float = Field(0.8, env="SIMILARITY_THRESHOLD")
    
    # Rate Limiting
    api_rate_limit: int = Field(10, env="API_RATE_LIMIT")  # requests per second
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()