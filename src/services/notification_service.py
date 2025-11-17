import boto3
from botocore.exceptions import ClientError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class NotificationService:
    def __init__(self, client, from_email: str):
        self.ses_client = client
        self.from_email = from_email

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=4),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(ClientError)
    )
    def send_donation_receipt(self, email_to: str, amount_cents: int, donation_id: str):
        amount_dollars = f"{(amount_cents / 100):.2f}"
        subject = "Thank you for your donation!"
        body_text = (
            f"Hello,\n\n"
            f"Thank you for your generous donation of ${amount_dollars}.\n"
            f"Your donation ID is: {donation_id}\n\n"
            f"We appreciate your support!"
        )
        
        print(f"Attempting to send email to {email_to}...")
        
        self.ses_client.send_email(
            Source=self.from_email,
            Destination={'ToAddresses': [email_to]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body_text}}
            }
        )
        
        print(f"Successfully sent receipt to {email_to}")