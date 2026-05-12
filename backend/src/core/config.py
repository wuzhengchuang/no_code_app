from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 2
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = False
    
    model_config = SettingsConfigDict(env_file=".env")

def get_settings() -> Settings:
    return Settings()
