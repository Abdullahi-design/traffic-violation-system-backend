from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+aiomysql://root:root123@localhost:3306/traffic_violation_db"
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440
    UPLOAD_DIR: str = "./uploads"
    CORS_ORIGINS: str = "http://localhost:3000"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
