from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import List, Optional
from functools import lru_cache

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "SecureFlow"
    DEBUG: bool = True
    VERSION: str = "1.0.0"
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/secureflow"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production-very-secret-key-12345"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8000", "http://127.0.0.1:5173", "http://127.0.0.1:3000"]
    
    # AWS (demo mode must be selected explicitly per connector)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_DEFAULT_REGION: str = "us-east-1"
    
    # GCP
    GCP_PROJECT_ID: Optional[str] = None
    GCP_CREDENTIALS_PATH: Optional[str] = None
    
    # Azure
    AZURE_SUBSCRIPTION_ID: Optional[str] = None
    AZURE_TENANT_ID: Optional[str] = None
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # ML Models
    ML_MODEL_PATH: str = "./models"
    ENABLE_ML_INFERENCE: bool = True
    HF_TOKEN: Optional[str] = None
    
    # Alerting
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: str = "alerts@secureflow.io"
    
    SLACK_WEBHOOK_URL: Optional[str] = None
    TEAMS_WEBHOOK_URL: Optional[str] = None
    PAGERDUTY_API_KEY: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    @model_validator(mode="after")
    def validate_production_signing_key(self):
        # DEBUG=False is the existing documented production switch.
        if not self.DEBUG:
            if (
                self.SECRET_KEY == Settings.model_fields["SECRET_KEY"].default
                or len(self.SECRET_KEY.strip()) < 32
                or self.SECRET_KEY.strip().lower() in {
                    "your-super-secret-key-change-this-in-production",
                    "change-this-secret-key-in-production",
                }
            ):
                raise ValueError(
                    "When DEBUG=False, set SECRET_KEY to a unique random value "
                    "of at least 32 characters."
                )
        return self

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
