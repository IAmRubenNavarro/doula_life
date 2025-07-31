"""
Minimal FastAPI app to test Stripe integration
"""
from fastapi import FastAPI, HTTPException
import stripe
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

app = FastAPI(title="Stripe Test App")

@app.get("/")
async def root():
    return {"message": "Stripe Test App is running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "stripe_configured": bool(stripe.api_key)}

@app.post("/test-payment-intent")
async def test_payment_intent(amount: int = 2000):
    """Test creating a payment intent"""
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    try:
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            metadata={'test': 'true'}
        )
        return {
            "payment_intent_id": intent.id,
            "client_secret": intent.client_secret,
            "amount": intent.amount,
            "status": intent.status
        }
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)