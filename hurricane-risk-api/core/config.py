"""
Configuration settings for Hurricane Risk API
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    WEATHER_LAB_API_URL: str = "https://weather-lab-data-api-production.up.railway.app"
    RISK_RADIUS_KM: float = 160.9  # 100 miles in kilometers
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"


settings = Settings()
