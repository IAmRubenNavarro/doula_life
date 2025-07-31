"""
Standalone Stripe Payment API - No Database Required
This version of your payment endpoints works without database dependencies
"""
from fastapi import FastAPI, HTTPException, Request
import stripe
import os
import logging
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

# Load environment variables
load_dotenv()

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Doula Life Stripe Payment API",
    description="Stripe payment processing endpoints",
    version="1.0.0"
)

# Pydantic models for request/response
class PaymentIntentCreate(BaseModel):
    amount: int  # Amount in cents
    currency: str = "usd"
    service_id: Optional[str] = None
    appointment_id: Optional[str] = None
    training_id: Optional[str] = None
    user_id: Optional[str] = None

class PaymentIntentResponse(BaseModel):
    client_secret: str
    payment_intent_id: str

@app.get("/")
async def root():
    return {"message": "Doula Life Stripe Payment API", "status": "running"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    stripe_configured = bool(os.getenv("STRIPE_SECRET_KEY"))
    webhook_configured = bool(os.getenv("STRIPE_WEBHOOK_SECRET"))
    
    return {
        "status": "healthy",
        "stripe_configured": stripe_configured,
        "webhook_configured": webhook_configured,
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.post("/payments/create-payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(payment_data: PaymentIntentCreate):
    """
    Create a Stripe Payment Intent for processing payments.
    
    This endpoint creates a Payment Intent with Stripe that allows the client
    to collect payment from customers. The Payment Intent includes metadata
    to track which service, appointment, or training the payment is for.
    """
    logger.info(f"Creating payment intent for amount: ${payment_data.amount/100:.2f} {payment_data.currency.upper()}")
    
    try:
        # Validate Stripe configuration
        if not stripe.api_key:
            logger.error("Stripe secret key not configured")
            raise HTTPException(
                status_code=500, 
                detail="Payment processing not configured"
            )
        
        # Build metadata dictionary for tracking payment context
        metadata = {}
        if payment_data.service_id:
            metadata["service_id"] = payment_data.service_id
            logger.debug(f"Adding service_id to metadata: {payment_data.service_id}")
        if payment_data.appointment_id:
            metadata["appointment_id"] = payment_data.appointment_id
            logger.debug(f"Adding appointment_id to metadata: {payment_data.appointment_id}")
        if payment_data.training_id:
            metadata["training_id"] = payment_data.training_id
            logger.debug(f"Adding training_id to metadata: {payment_data.training_id}")
        if payment_data.user_id:
            metadata["user_id"] = payment_data.user_id
            logger.debug(f"Adding user_id to metadata: {payment_data.user_id}")
        
        # Validate amount
        if payment_data.amount <= 0:
            logger.warning(f"Invalid payment amount: {payment_data.amount}")
            raise HTTPException(
                status_code=400, 
                detail="Payment amount must be greater than zero"
            )
        
        if payment_data.amount > 999999:  # $9,999.99 max
            logger.warning(f"Payment amount too large: {payment_data.amount}")
            raise HTTPException(
                status_code=400, 
                detail="Payment amount exceeds maximum allowed"
            )
        
        logger.info(f"Creating Stripe Payment Intent with metadata: {metadata}")
        
        # Create payment intent with Stripe API
        intent = stripe.PaymentIntent.create(
            amount=payment_data.amount,
            currency=payment_data.currency,
            metadata=metadata,
            automatic_payment_methods={'enabled': True},
            description=f"Doula Life payment - {metadata.get('service_id', 'general')}"
        )
        
        logger.info(f"Successfully created Payment Intent: {intent.id}")
        
        return PaymentIntentResponse(
            client_secret=intent.client_secret,
            payment_intent_id=intent.id
        )
        
    except stripe.error.InvalidRequestError as e:
        logger.error(f"Invalid Stripe request: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid payment parameters: {str(e)}")
    except stripe.error.AuthenticationError as e:
        logger.error(f"Stripe authentication error: {str(e)}")
        raise HTTPException(status_code=500, detail="Payment service authentication failed")
    except stripe.error.APIConnectionError as e:
        logger.error(f"Stripe API connection error: {str(e)}")
        raise HTTPException(status_code=503, detail="Payment service temporarily unavailable")
    except stripe.error.RateLimitError as e:
        logger.error(f"Stripe rate limit exceeded: {str(e)}")
        raise HTTPException(status_code=429, detail="Too many payment requests, please try again later")
    except stripe.error.StripeError as e:
        logger.error(f"General Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Payment processing error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error creating payment intent: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while processing payment")

@app.post("/payments/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events for payment processing.
    
    This is a simplified version that logs events but doesn't save to database.
    In production, you would save successful payments to your database.
    """
    logger.info("Received Stripe webhook event")
    
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    if not sig_header:
        logger.error("Missing Stripe signature header")
        raise HTTPException(status_code=400, detail="Missing webhook signature")
    
    try:
        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        if not webhook_secret:
            logger.error("Stripe webhook secret not configured")
            raise HTTPException(status_code=500, detail="Webhook processing not configured")
        
        # Verify webhook signature
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        logger.info(f"Successfully verified webhook event: {event['type']} (ID: {event['id']})")
        
        # Handle different event types
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            logger.info(f"✅ Payment succeeded: {payment_intent['id']}")
            logger.info(f"   Amount: ${payment_intent['amount']/100:.2f}")
            logger.info(f"   Metadata: {payment_intent.get('metadata', {})}")
            
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            failure_reason = payment_intent.get('last_payment_error', {}).get('message', 'Unknown')
            logger.warning(f"❌ Payment failed: {payment_intent['id']} - Reason: {failure_reason}")
            
        elif event['type'] == 'payment_intent.requires_action':
            payment_intent = event['data']['object']
            logger.info(f"⚠️  Payment requires additional action: {payment_intent['id']}")
            
        elif event['type'] == 'payment_intent.canceled':
            payment_intent = event['data']['object']
            logger.info(f"🚫 Payment canceled: {payment_intent['id']}")
            
        else:
            logger.info(f"📝 Received unhandled webhook event type: {event['type']}")
        
        return {"status": "success", "event_id": event['id']}
        
    except ValueError as e:
        logger.error(f"Invalid JSON payload in webhook: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid webhook payload format")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Webhook signature verification failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    except Exception as e:
        logger.error(f"Unexpected error processing webhook event: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error processing webhook event")

@app.get("/payments/test")
async def test_stripe_config():
    """Test Stripe configuration and connectivity"""
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    try:
        # Test Stripe connection
        account = stripe.Account.retrieve()
        return {
            "stripe_connected": True,
            "account_id": account.id,
            "business_name": account.business_profile.get('name', 'N/A'),
            "country": account.country,
            "charges_enabled": account.charges_enabled,
            "payouts_enabled": account.payouts_enabled
        }
    except stripe.error.StripeError as e:
        logger.error(f"Stripe configuration test failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)