import boto3
import stripe
from functools import lru_cache

from src.core.config import settings
from src.data_access.dynamodb import DynamoDataAccess
from src.services.donation_service import DonationService
from src.services.notification_service import NotificationService


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
    table = dynamo_resource.Table(settings.DYNAMODB_TABLE_NAME)
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
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    session = get_boto_session()
    sqs_client = session.client('sqs')
    
    return DonationService(
        repository=get_dynamo_table(),
        sqs_client=sqs_client,
        payment_queue_url=settings.PAYMENT_QUEUE_URL,
        notification_queue_url=settings.NOTIFICATION_QUEUE_URL,
        stripe_webhook_secret=settings.STRIPE_WEBHOOK_SECRET
    )


dynamo_table = get_dynamo_table()
notification_service = get_notification_service()
donation_service = get_donation_service()