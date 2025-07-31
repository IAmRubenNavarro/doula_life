"""
Unified Payment API - Stripe + PayPal Integration
This app supports both Stripe and PayPal payments with a unified interface
"""
from fastapi import FastAPI, HTTPException, Request
import stripe
import paypalrestsdk
import os
import logging
import json
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Doula Life Unified Payment API",
    description="Unified payment processing with Stripe and PayPal support",
    version="1.0.0"
)

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Configure PayPal
paypalrestsdk.configure({
    "mode": os.getenv("PAYPAL_MODE", "sandbox"),  # sandbox or live
    "client_id": os.getenv("PAYPAL_CLIENT_ID"),
    "client_secret": os.getenv("PAYPAL_CLIENT_SECRET")
})

# ========================
# Pydantic Models
# ========================

class UnifiedPaymentCreate(BaseModel):
    amount: float  # Amount in dollars
    currency: str = "USD"
    payment_provider: str = Field(..., pattern="^(stripe|paypal)$")
    service_id: Optional[str] = None
    appointment_id: Optional[str] = None
    training_id: Optional[str] = None
    user_id: Optional[str] = None
    # PayPal-specific fields
    return_url: Optional[str] = None
    cancel_url: Optional[str] = None

class UnifiedPaymentResponse(BaseModel):
    provider: str
    payment_id: str
    client_secret: Optional[str] = None  # Stripe only
    approval_url: Optional[str] = None   # PayPal only
    status: str

class StripePaymentIntent(BaseModel):
    amount: int  # Amount in cents
    currency: str = "usd"
    service_id: Optional[str] = None
    appointment_id: Optional[str] = None
    training_id: Optional[str] = None
    user_id: Optional[str] = None

class PayPalOrder(BaseModel):
    amount: float  # Amount in dollars
    currency: str = "USD"
    service_id: Optional[str] = None
    appointment_id: Optional[str] = None
    training_id: Optional[str] = None
    user_id: Optional[str] = None
    return_url: str
    cancel_url: str

# ========================
# Health & Info Endpoints
# ========================

@app.get("/")
async def root():
    return {"message": "Doula Life Unified Payment API", "status": "running", "providers": ["stripe", "paypal"]}

@app.get("/health")
async def health():
    """Health check endpoint with payment provider status"""
    stripe_configured = bool(os.getenv("STRIPE_SECRET_KEY"))
    paypal_configured = bool(os.getenv("PAYPAL_CLIENT_ID") and os.getenv("PAYPAL_CLIENT_SECRET"))
    
    return {
        "status": "healthy",
        "providers": {
            "stripe": {
                "configured": stripe_configured,
                "ready": stripe_configured
            },
            "paypal": {
                "configured": paypal_configured,
                "mode": os.getenv("PAYPAL_MODE", "sandbox"),
                "ready": paypal_configured
            }
        },
        "environment": os.getenv("ENVIRONMENT", "development")
    }

# ========================
# Unified Payment Interface
# ========================

@app.post("/payments/create", response_model=UnifiedPaymentResponse)
async def create_unified_payment(payment_data: UnifiedPaymentCreate):
    """
    Create a payment using either Stripe or PayPal.
    
    Example usage:
    
    Stripe:
    {
        "amount": 20.00,
        "payment_provider": "stripe",
        "user_id": "123"
    }
    
    PayPal:
    {
        "amount": 20.00,
        "payment_provider": "paypal",
        "user_id": "123",
        "return_url": "https://yoursite.com/success",
        "cancel_url": "https://yoursite.com/cancel"
    }
    """
    logger.info(f"Creating unified payment: {payment_data.payment_provider}, ${payment_data.amount:.2f}")
    
    try:
        if payment_data.payment_provider == "stripe":
            return await create_stripe_payment(payment_data)
        elif payment_data.payment_provider == "paypal":
            return await create_paypal_payment(payment_data)
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid payment provider. Must be 'stripe' or 'paypal'"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in unified payment: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing payment"
        )

# ========================
# Stripe Implementation
# ========================

async def create_stripe_payment(payment_data: UnifiedPaymentCreate) -> UnifiedPaymentResponse:
    """Create Stripe payment intent"""
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    try:
        # Convert dollars to cents for Stripe
        amount_cents = int(payment_data.amount * 100)
        
        # Build metadata
        metadata = {}
        if payment_data.user_id:
            metadata["user_id"] = payment_data.user_id
        if payment_data.service_id:
            metadata["service_id"] = payment_data.service_id
        if payment_data.appointment_id:
            metadata["appointment_id"] = payment_data.appointment_id
        if payment_data.training_id:
            metadata["training_id"] = payment_data.training_id
        
        # Create payment intent
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency=payment_data.currency.lower(),
            metadata=metadata,
            automatic_payment_methods={'enabled': True},
            description=f"Doula Life payment - {metadata.get('service_id', 'general')}"
        )
        
        logger.info(f"Created Stripe payment intent: {intent.id}")
        
        return UnifiedPaymentResponse(
            provider="stripe",
            payment_id=intent.id,
            client_secret=intent.client_secret,
            status="requires_payment_method"
        )
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")

@app.post("/payments/stripe/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing signature")
    
    try:
        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        if not webhook_secret:
            raise HTTPException(status_code=500, detail="Webhook secret not configured")
        
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            logger.info(f"✅ Stripe payment succeeded: {payment_intent['id']}")
            # Here you would save to database
            
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            logger.warning(f"❌ Stripe payment failed: {payment_intent['id']}")
        
        return {"status": "success", "event_id": event['id']}
        
    except Exception as e:
        logger.error(f"Stripe webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail="Webhook processing failed")

# ========================
# PayPal Implementation
# ========================

async def create_paypal_payment(payment_data: UnifiedPaymentCreate) -> UnifiedPaymentResponse:
    """Create PayPal payment order"""
    if not os.getenv("PAYPAL_CLIENT_ID"):
        raise HTTPException(status_code=500, detail="PayPal not configured")
    
    if not payment_data.return_url or not payment_data.cancel_url:
        raise HTTPException(
            status_code=400,
            detail="PayPal payments require return_url and cancel_url"
        )
    
    try:
        # Build custom data
        custom_data = {
            "user_id": payment_data.user_id,
            "service_id": payment_data.service_id,
            "appointment_id": payment_data.appointment_id,
            "training_id": payment_data.training_id,
        }
        custom_data = {k: v for k, v in custom_data.items() if v is not None}
        
        # Create PayPal payment
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "redirect_urls": {
                "return_url": payment_data.return_url,
                "cancel_url": payment_data.cancel_url
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": "Doula Life Service",
                        "sku": custom_data.get("service_id", "general"),
                        "price": f"{payment_data.amount:.2f}",
                        "currency": payment_data.currency,
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": f"{payment_data.amount:.2f}",
                    "currency": payment_data.currency
                },
                "description": f"Doula Life payment - {custom_data.get('service_id', 'general')}",
                "custom": json.dumps(custom_data) if custom_data else ""
            }]
        })
        
        if payment.create():
            # Find approval URL
            approval_url = None
            for link in payment.links:
                if link.rel == "approval_url":
                    approval_url = link.href
                    break
            
            if not approval_url:
                raise HTTPException(status_code=500, detail="PayPal approval URL not found")
            
            logger.info(f"Created PayPal payment: {payment.id}")
            
            return UnifiedPaymentResponse(
                provider="paypal",
                payment_id=payment.id,
                approval_url=approval_url,
                status="created"
            )
        else:
            raise HTTPException(status_code=400, detail=f"PayPal error: {payment.error}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PayPal error: {str(e)}")
        raise HTTPException(status_code=500, detail="PayPal payment creation failed")

@app.post("/payments/paypal/capture/{payment_id}")
async def capture_paypal_payment(payment_id: str, payer_id: str):
    """Capture PayPal payment after approval"""
    logger.info(f"Capturing PayPal payment: {payment_id}")
    
    try:
        payment = paypalrestsdk.Payment.find(payment_id)
        
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        if payment.execute({"payer_id": payer_id}):
            logger.info(f"✅ PayPal payment captured: {payment.id}")
            
            transaction = payment.transactions[0]
            return {
                "status": "success",
                "payment_id": payment.id,
                "payer_id": payer_id,
                "amount": transaction.amount.total,
                "currency": transaction.amount.currency,
                "state": payment.state
            }
        else:
            raise HTTPException(status_code=400, detail=f"Capture failed: {payment.error}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PayPal capture error: {str(e)}")
        raise HTTPException(status_code=500, detail="Payment capture failed")

@app.post("/payments/paypal/webhook")
async def paypal_webhook(request: Request):
    """
    Handle PayPal webhook events.
    
    Note: This is a simplified webhook handler for the standalone app.
    In the main application, webhook handling includes database operations.
    """
    logger.info("Received PayPal webhook event")
    
    try:
        payload = await request.body()
        
        if not payload:
            logger.error("Empty PayPal webhook payload")
            raise HTTPException(status_code=400, detail="Empty webhook payload")
        
        # Parse JSON payload
        try:
            event_data = json.loads(payload.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"Invalid JSON in PayPal webhook payload: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid webhook payload format")
        
        # Extract event information
        event_type = event_data.get('event_type')
        event_id = event_data.get('id', 'unknown')
        
        if not event_type:
            logger.error("PayPal webhook missing event_type")
            raise HTTPException(status_code=400, detail="Invalid webhook event format")
        
        logger.info(f"Processing PayPal webhook event: {event_type} (ID: {event_id})")
        
        # Handle different event types
        if event_type == 'PAYMENT.SALE.COMPLETED':
            resource = event_data.get('resource', {})
            payment_id = resource.get('parent_payment', resource.get('id'))
            sale_id = resource.get('id')
            amount = resource.get('amount', {})
            
            logger.info(f"PayPal sale completed: {sale_id} for payment: {payment_id}")
            logger.info(f"Amount: {amount.get('total', '0.00')} {amount.get('currency', 'USD')}")
            
        elif event_type == 'PAYMENT.SALE.DENIED':
            resource = event_data.get('resource', {})
            sale_id = resource.get('id')
            logger.warning(f"PayPal sale denied: {sale_id}")
            
        elif event_type == 'PAYMENT.SALE.REFUNDED':
            resource = event_data.get('resource', {})
            refund_id = resource.get('id')
            amount = resource.get('amount', {})
            logger.info(f"PayPal refund: {refund_id}, Amount: {amount.get('total', '0.00')}")
            
        else:
            logger.info(f"Unhandled PayPal webhook event: {event_type}")
        
        return {"status": "success", "event_id": event_id, "event_type": event_type}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PayPal webhook processing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing webhook event")

# ========================
# Test & Utility Endpoints
# ========================

@app.post("/payments/test")
async def test_payment_providers():
    """Test both payment providers"""
    results = {"stripe": None, "paypal": None}
    
    # Test Stripe
    if stripe.api_key:
        try:
            account = stripe.Account.retrieve()
            results["stripe"] = {
                "status": "connected",
                "account_id": account.id,
                "country": account.country
            }
        except Exception as e:
            results["stripe"] = {"status": "error", "message": str(e)}
    else:
        results["stripe"] = {"status": "not_configured"}
    
    # Test PayPal
    if os.getenv("PAYPAL_CLIENT_ID"):
        try:
            # Test by creating a minimal payment (not executed)
            test_payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {"payment_method": "paypal"},
                "redirect_urls": {
                    "return_url": "http://test.com/return",
                    "cancel_url": "http://test.com/cancel"
                },
                "transactions": [{
                    "amount": {"total": "1.00", "currency": "USD"},
                    "description": "Test payment"
                }]
            })
            
            # Don't actually create, just test configuration
            results["paypal"] = {
                "status": "configured",
                "mode": os.getenv("PAYPAL_MODE", "sandbox")
            }
        except Exception as e:
            results["paypal"] = {"status": "error", "message": str(e)}
    else:
        results["paypal"] = {"status": "not_configured"}
    
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, reload=True)