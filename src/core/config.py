from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    
    STRIPE_PUBLISHABLE_KEY: str
    STRIPE_SECRET_KEY: str

    AWS_REGION: str
    NOTIFICATION_QUEUE_URL: str
    PAYMENT_QUEUE_URL: str
    DYNAMODB_TABLE_NAME: str
    COGNITO_USER_POOL_ID: str
    COGNITO_USER_POOL_CLIENT_ID: str
    SES_FROM_EMAIL: str

    model_config = SettingsConfigDict(
        env_file=".env",            
        env_file_encoding="utf-8",
        case_sensitive=False,      
        extra="ignore"            
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()