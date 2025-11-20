import boto3
import stripe
from functools import lru_cache

from core.config import settings
from data_access.dynamodb import DynamoDataAccess
from services.donation_service import DonationService
from services.notification_service import NotificationService


@lru_cache()
def get_boto_session() -> boto3.Session:
    return boto3.Session(
        region_name=settings.AWS_REGION,
        profile_name=settings.AWS_PROFILE  
    )

@lru_cache()
def get_dynamo_table() -> DynamoDataAccess:
    session = get_boto_session()
    dynamo_resource = session.resource('dynamodb')
    table = dynamo_resource.Table(settings.DYNAMO_TABLE_NAME)
    return DynamoDataAccess(table=table)

@lru_cache()
def get_notification_service() -> NotificationService:
    session = get_boto_session()
    ses_client = session.client('ses')
    return NotificationService(
        client=ses_client, 
        from_email=settings.SES_FROM_EMAIL
    )

@lru_cache()
def get_donation_service() -> DonationService:
    if not settings.STRIPE_SECRET_KEY:
        raise ValueError("STRIPE_SECRET_KEY is required. Set it in SSM Parameter Store as /donate-now/STRIPE_SECRET_KEY or as an environment variable.")
    
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise ValueError("STRIPE_WEBHOOK_SECRET is required. Set it in SSM Parameter Store as /donate-now/STRIPE_WEBHOOK_SECRET or as an environment variable.")
    
    session = get_boto_session()
    sqs_client = session.client('sqs')
    
    return DonationService(
        data_access=get_dynamo_table(),
        sqs_client=sqs_client,
        payment_queue_url=settings.PAYMENT_QUEUE_URL,
        notification_queue_url=settings.NOTIFICATION_QUEUE_URL,
        stripe_webhook_secret=settings.STRIPE_WEBHOOK_SECRET
    )


dynamo_table = get_dynamo_table()
notification_service = get_notification_service()
donation_service = get_donation_service()