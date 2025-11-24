from fastapi import (
    APIRouter, 
    Request, 
    Header, 
    Depends, 
    HTTPException
)
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from typing import Optional
import stripe
import logging

from core.dependencies import donation_service
from api.schemas import CognitoUser, DonationIntentRequest, DonationIntentResponse, PublicDonationResponse, TotalDonationResponse

router = APIRouter()
security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)

async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(security)
) -> CognitoUser:
    try:
        auth = request.scope.get("aws.event", {}).get("requestContext", {}).get("authorizer", {})
        claims = auth.get("claims", {})
        
        if not claims:
            raise HTTPException(status_code=401, detail="Could not find user claims")

        user = CognitoUser(**claims)
        
        if not user.email_verified:
            raise HTTPException(status_code=403, detail="Email not verified")
            
        return user

    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid authentication credentials: {e}"
        )

@router.post(
    "/donations/create-intent",
    response_model=DonationIntentResponse
)
async def create_donation_intent(
    body: DonationIntentRequest,
    user: CognitoUser = Depends(get_current_user) 
):
    try:
        client_secret = donation_service.create_stripe_intent(
            amount=body.amount,
            email=user.email,      
            user_id=user.sub,
            user_name = user.name        
        )
        return DonationIntentResponse(client_secret=client_secret)
    
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")


@router.post("/webhooks/stripe")
async def handle_stripe_webhook(request: Request, stripe_signature: str = Header(...)):
    """
    Receives webhook events from Stripe, validates them,
    and queues them in SQS for background processing.
    """
    payload = await request.body()
    
    try:
        donation_service.queue_payment_webhook(
            payload=payload,
            signature_header=stripe_signature
        )
        
        return {"status": "queued"}
    
    except stripe.error.SignatureVerificationError as e:
        logger.warning(f"Webhook signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except ValueError as e:
        logger.warning(f"Webhook invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except Exception as e:
        logger.error(f"Webhook internal error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get(
    "/donations/recent",
    response_model=list[PublicDonationResponse]
)
def get_recent_donations():
    donations = donation_service.list_recent_donations(limit=10)
    return donations

@router.get(
    "/donations/total",
    response_model=TotalDonationResponse
)
def get_total_donations():
    total_cents_data = donation_service.get_total_donations()
    total_cents = total_cents_data.get('TotalAmountCents', 0)
    
    total_amount_dollars = total_cents / 100.0
        
    return TotalDonationResponse(total_amount_dollars=total_amount_dollars)