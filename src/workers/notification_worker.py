import json
import logging
from core.dependencies import notification_service

# We need to configure logging here since workers are entry points
from core.logging_config import configure_logging
configure_logging()

logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    logger.info(f"Received {len(event['Records'])} notification jobs.")

    for record in event['Records']:
        try:
            job = json.loads(record['body'])
            
            if job.get("type") == "RECEIPT":
                notification_service.send_donation_receipt(
                    email_to=job['email_to'],
                    amount_cents=job['amount_cents'],
                    donation_id=job['donation_id']
                )
        
        except Exception as e:
            logger.error(f"CRITICAL: Failed to process message {record['messageId']}. Error: {e}")           
            raise e
            
    return {'statusCode': 200}