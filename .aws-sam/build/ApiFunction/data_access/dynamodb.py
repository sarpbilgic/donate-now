import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from datetime import datetime
from typing import Any
from src.models.donation import UserProfile, Donation

USER_PREFIX = "USER#"
DONATION_PREFIX = "DONATION#"
PROFILE_SK = "PROFILE"


class DynamoDataAccess:
    def __init__(self, table):
        self.table = table

    def create_user_profile(self, profile: UserProfile) -> dict:
        item = {
            "PK": f"{USER_PREFIX}{profile.email}",
            "SK": PROFILE_SK,
            "email": profile.email,
            "name": profile.name,
            "user_id": profile.user_id,
            "created_at": profile.created_at.isoformat()
        }
        
        try:
            self.table.put_item(
                Item=item,
                ConditionExpression="attribute_not_exists(PK)"
            )
            return item
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                print(f"User profile already exists for {profile.email}")
                return self.get_user_profile(profile.email)
            else:
                raise

    def get_user_profile(self, email: str) -> dict | None:
        key = {
            "PK": f"{USER_PREFIX}{email}",
            "SK": PROFILE_SK
        }
        response = self.table.get_item(Key=key)
        return response.get("Item")

    def create_donation_record(self, donation: Donation) -> dict:
        item = {
            "PK": f"{USER_PREFIX}{donation.user_email}",
            "SK": f"{DONATION_PREFIX}{donation.donation_id}",
            "donation_id": donation.donation_id,
            "user_email": donation.user_email,
            "amount": donation.amount,
            "currency": donation.currency,
            "status": donation.status,
            "stripe_payment_intent_id": donation.stripe_payment_intent_id,
            "created_at": donation.created_at.isoformat()
        }
        
        self.table.put_item(Item=item)
        return item

    def update_donation_status(self, user_email: str, donation_id: str, 
                               status: str, payment_intent_id: str) -> dict:
        try:                       
            response = self.table.update_item(
                Key={
                    "PK": f"{USER_PREFIX}{user_email}",
                    "SK": f"{DONATION_PREFIX}{donation_id}"
                },
                UpdateExpression="SET #status = :s, #stripe_id = :pid",
                ConditionExpression="#status <> :s",
                ExpressionAttributeNames={
                    "#status": "status",
                    "#stripe_id": "stripe_payment_intent_id"
                },
                ExpressionAttributeValues={
                    ":s": status,
                    ":pid": payment_intent_id
                },
                ReturnValues="ALL_NEW"
            )
            return response.get("Attributes", {})
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                print(f"Idempotency check: Donation {donation_id} status is already {status}.")
                return None 
            else:
                print(f"Error updating donation status: {e}")
                raise

    def list_donations_by_user(self, email: str) -> list[dict]:
        response = self.table.query(
            KeyConditionExpression=Key("PK").eq(f"{USER_PREFIX}{email}") & 
                                 Key("SK").begins_with(DONATION_PREFIX)
        )
        return response.get("Items", [])