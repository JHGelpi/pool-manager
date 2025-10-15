from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DB_USER: str = "pooluser"
    DB_PASSWORD: str = "poolpass"
    DB_NAME: str = "pooldb"
    DATABASE_URL: str = "postgresql+asyncpg://pooluser:poolpass@db:5432/pooldb"
    
    # Application
    SECRET_KEY: str = "change-this-to-a-random-secret-key"
    DEBUG: bool = False
    DEFAULT_USER_EMAIL: str = "admin@example.com"
    
    # SMTP
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_TLS: bool = True
    
    # Scheduler
    SCHEDULER_ENABLED: bool = True

    # Timezone
    TIMEZONE: str = "America/New_York"  # Default to Eastern Time

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()