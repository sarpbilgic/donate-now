import json
import stripe
import logging
from botocore.exceptions import ClientError

from data_access.dynamodb import DynamoDataAccess
from models.donation import Donation, UserProfile

logger = logging.getLogger(__name__)

class DonationService:
    def __init__(
        self,
        data_access: DynamoDataAccess,
        sqs_client,
        payment_queue_url: str,
        notification_queue_url: str,
        stripe_webhook_secret: str
    ):
        self.data_access = data_access
        self.sqs_client = sqs_client
        self.payment_queue_url = payment_queue_url
        self.notification_queue_url = notification_queue_url
        self.stripe_webhook_secret = stripe_webhook_secret

    def create_stripe_intent(self, amount: int, email: str, user_id: str, user_name: str = None) -> str:
        profile = UserProfile(email=email, user_id=user_id, name=user_name)
        self.data_access.create_user_profile(profile)
        
        donation = Donation(
            user_email=email, 
            amount=amount, 
            status="PENDING", 
            donor_name=user_name if user_name else None
        )
        self.data_access.create_donation_record(donation)
        
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency="usd",
                automatic_payment_methods={"enabled": True},
                metadata={
                    "user_email": email,
                    "donation_id": donation.donation_id
                }
            )
            return intent.client_secret
        except Exception as e:
            logger.error(f"Error creating Stripe intent: {e}")
            raise

    def queue_payment_webhook(self, payload: bytes, signature_header: str):
        try:
            event = stripe.Webhook.construct_event(
                payload=payload, 
                sig_header=signature_header, 
                secret=self.stripe_webhook_secret
            )
            
            self.sqs_client.send_message(
                QueueUrl=self.payment_queue_url,
                MessageBody=json.dumps(event)
            )
        except ValueError as e:
            logger.error(f"Webhook error: Invalid payload - {e}")
            raise
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            logger.error(f"Webhook error: Invalid signature - {e}")
            raise
        except ClientError as e:
            logger.error(f"SQS Error: {e}")
            raise

    def handle_payment_event(self, event_body: str):
        event = json.loads(event_body)
        
        if event['type'] == 'payment_intent.succeeded':
            
            intent = event['data']['object']
            
            metadata = intent['metadata']
            email = metadata['user_email']
            donation_id = metadata['donation_id']
            payment_intent_id = intent['id']
            amount = intent['amount']

            updated_attributes = self.data_access.update_donation_status(
                user_email=email,
                donation_id=donation_id,
                status="SUCCEEDED",
                payment_intent_id=payment_intent_id
            )

            if updated_attributes:

                self.data_access.update_total_donations(amount)

                notification_job = {
                    "type": "RECEIPT",
                    "email_to": email,
                    "amount_cents": amount,
                    "donation_id": donation_id
                }
                self.sqs_client.send_message(
                    QueueUrl=self.notification_queue_url,
                    MessageBody=json.dumps(notification_job)
                )
                logger.info(f"Successfully processed payment {payment_intent_id}.")
            else:
                logger.info(f"Skipped duplicate processing for payment {payment_intent_id}.")

        elif event['type'] == 'payment_intent.failed':
            intent = event['data']['object']
            metadata = intent['metadata']
            email = metadata['user_email']
            donation_id = metadata['donation_id']
            payment_intent_id = intent['id']

            updated_attributes = self.data_access.update_donation_status(
                user_email=email,
                donation_id=donation_id,
                status="FAILED",
                payment_intent_id=payment_intent_id
            )
            
            if updated_attributes:
                logger.warning(f"Payment failed for donation {donation_id}.")
            else:
                logger.info(f"Skipped duplicate processing for failed payment {donation_id}.")
        
        else:
            logger.warning(f"Received unhandled event type: {event['type']}")


    def list_recent_donations(self, limit: int = 10) -> list[dict]:
        return self.data_access.get_recent_donations(limit)

    def get_total_donations(self) -> dict:
        return self.data_access.get_total_donations()