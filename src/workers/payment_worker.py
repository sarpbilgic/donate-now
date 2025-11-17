from src.core.dependencies import donation_service

def lambda_handler(event, context):
    print(f"Received {len(event['Records'])} payment events.")
    
    for record in event['Records']:
        event_body = record['body']
        try:
            donation_service.handle_payment_event(event_body)
        except Exception as e:
            print(f"Error processing payment event: {e}")
            
    return {'statusCode': 200}