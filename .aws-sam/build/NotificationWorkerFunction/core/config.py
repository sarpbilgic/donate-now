import boto3
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    AWS_PROFILE: Optional[str] = None
    AWS_REGION: str = "eu-central-1"
    NOTIFICATION_QUEUE_URL: str
    PAYMENT_QUEUE_URL: str
    DYNAMO_TABLE_NAME: str
    COGNITO_USER_POOL_ID: Optional[str] = None
    COGNITO_USER_POOL_CLIENT_ID: Optional[str] = None
    SES_FROM_EMAIL: Optional[str] = "sarpemrebilgic@gmail.com"

    model_config = SettingsConfigDict(
        env_file=".env",            
        env_file_encoding="utf-8",
        case_sensitive=False,      
        extra="ignore"            
    )
    
def _get_ssm_parameter(parameter_name: str, region: str = "eu-central-1") -> Optional[str]:
    """Fetch parameter from SSM Parameter Store"""
    try:
        ssm_client = boto3.client('ssm', region_name=region)
        response = ssm_client.get_parameter(
            Name=parameter_name,
            WithDecryption=True
        )
        return response['Parameter']['Value']
    except Exception as e:
        print(f"Warning: Could not fetch SSM parameter {parameter_name}: {e}")
        return None

@lru_cache()
def get_settings() -> Settings:
    """Get settings, fetching from SSM if not in environment variables"""
    settings = Settings()
    
    # Read from SSM Parameter Store if not set in environment variables
    if not settings.STRIPE_SECRET_KEY:
        region = settings.AWS_REGION or os.getenv('AWS_REGION', 'eu-central-1')
        settings.STRIPE_SECRET_KEY = _get_ssm_parameter("/donate-now/STRIPE_SECRET_KEY", region)
    
    if not settings.STRIPE_WEBHOOK_SECRET:
        region = settings.AWS_REGION or os.getenv('AWS_REGION', 'eu-central-1')
        settings.STRIPE_WEBHOOK_SECRET = _get_ssm_parameter("/donate-now/STRIPE_WEBHOOK_SECRET", region)
    
    return settings

settings = get_settings()