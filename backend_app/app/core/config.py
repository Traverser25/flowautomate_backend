from functools import lru_cache
from pydantic import BaseSettings, AnyUrl, Field
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "backend_app"
    DEBUG: bool = False

    # MongoDB
    MONGO_URL: AnyUrl = Field("mongodb://localhost:27017", env="MONGO_URL")
    MONGO_DB: str = Field("backend_app", env="MONGO_DB")

    # JWT
    JWT_SECRET: str = Field("change-this-in-prod", env="JWT_SECRET")
    JWT_ALG: str = Field("HS256", env="JWT_ALG")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    # Rate Limiter
    RATE_LIMIT_MAX: int = Field(60, env="RATE_LIMIT_MAX")           # max requests
    RATE_LIMIT_WINDOW_SEC: int = Field(60, env="RATE_LIMIT_WINDOW_SEC")  # per seconds

    # Optional bootstrap admin email
    #ADMIN_EMAIL: Optional[str] = Field(None, env="ADMIN_EMAIL")

    # Pinecone
    PINECONE_API_KEY: str = Field(..., env="PINECONE_API_KEY")
    PINECONE_INDEX_NAME: str = Field("automateflow", env="PINECONE_INDEX_NAME")

    # Groq
    GROQ_API_KEY: str = Field(..., env="GROQ_API_KEY")
    GROQ_MODEL_NAME: str = Field("llama-3.3-70b-versatile", env="GROQ_MODEL_NAME")
 

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()
