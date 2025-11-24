from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class DonationIntentRequest(BaseModel):
    amount: int  

class DonationIntentResponse(BaseModel):
    client_secret: str

class CognitoUser(BaseModel):
    sub: str  # The unique user ID from Cognito
    email: EmailStr
    email_verified: bool
    name: Optional[str] = None

class PublicDonationResponse(BaseModel):
    donor_name: str
    amount: int
    currency: str
    created_at: datetime

class TotalDonationResponse(BaseModel):
    total_amount_dollars: float