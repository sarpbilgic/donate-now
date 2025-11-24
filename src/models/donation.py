import uuid
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from typing import Literal


DonationStatus = Literal["PENDING", "SUCCEEDED", "FAILED"]

class UserProfile(BaseModel):
    email: EmailStr
    name: str | None = None
    user_id: str  # The 'sub' from the Cognito JWT
    created_at: datetime = Field(default_factory=datetime.now)

class Donation(BaseModel):
    user_email: EmailStr
    donor_name: str | None = None
    donation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    amount: int 
    currency: str = "usd"
    status: DonationStatus = "PENDING"
    
    stripe_payment_intent_id: str | None = None
    
    created_at: datetime = Field(default_factory=datetime.now)