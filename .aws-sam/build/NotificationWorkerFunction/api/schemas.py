from pydantic import BaseModel, EmailStr
from typing import Optional

class DonationIntentRequest(BaseModel):
    amount: int  

class DonationIntentResponse(BaseModel):
    """The response sent back to the client."""
    client_secret: str

class CognitoUser(BaseModel):
    """
    Pydantic model to validate and hold the authenticated user's
    data, which we get from the Cognito JWT claims.
    """
    sub: str  # The unique user ID from Cognito
    email: EmailStr
    email_verified: bool
    # Add other claims like 'name' if you need them
    name: Optional[str] = None