"""
Simple Stripe test script (Windows compatible)
"""
import os
import stripe
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_stripe():
    """Test basic Stripe functionality"""
    print("Testing Stripe Integration...")
    print("=" * 40)
    
    # Check if Stripe secret key is configured
    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe_key:
        print("[FAIL] STRIPE_SECRET_KEY not found in environment")
        print("Add STRIPE_SECRET_KEY=sk_test_... to your .env file")
        return
    
    print(f"[PASS] Found Stripe key: {stripe_key[:8]}...")
    
    # Configure Stripe
    stripe.api_key = stripe_key
    
    try:
        # Test connection
        print("\nTesting Stripe connection...")
        account = stripe.Account.retrieve()
        print(f"[PASS] Connected to Stripe account: {account.id}")
        print(f"       Country: {account.country}")
        
        # Test payment intent creation
        print("\nTesting payment intent creation...")
        intent = stripe.PaymentIntent.create(
            amount=2000,  # $20.00
            currency='usd',
            metadata={'test': 'true'}
        )
        print(f"[PASS] Created payment intent: {intent.id}")
        print(f"       Amount: ${intent.amount / 100:.2f}")
        print(f"       Status: {intent.status}")
        
        print("\n[SUCCESS] All tests passed!")
        print("\nNext steps:")
        print("1. Install remaining dependencies if needed")
        print("2. Run: uvicorn app.main:app --reload")
        print("3. Test endpoints at: http://localhost:8000/docs")
        
    except stripe.error.AuthenticationError:
        print("[FAIL] Invalid Stripe API key")
    except Exception as e:
        print(f"[FAIL] Error: {str(e)}")

if __name__ == "__main__":
    test_stripe()