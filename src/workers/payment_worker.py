import logging
from core.dependencies import donation_service

# We need to configure logging here since workers are entry points
from core.logging_config import configure_logging
configure_logging()

logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    logger.info(f"Received {len(event['Records'])} payment events.")
    
    for record in event['Records']:
        event_body = record['body']
        try:
            donation_service.handle_payment_event(event_body)
        except Exception as e:
            logger.error(f"Error processing payment event: {e}")
            raise e
            
    return {'statusCode': 200}