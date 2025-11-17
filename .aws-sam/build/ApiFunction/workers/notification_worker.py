import json
from src.core.dependencies import notification_service

def lambda_handler(event, context):
    print(f"Received {len(event['Records'])} notification jobs.")

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
            print(f"CRITICAL: Failed to process message {record['messageId']}. Error: {e}")           
            raise e
            
    return {'statusCode': 200}