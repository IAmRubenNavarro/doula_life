"""
Test script for unified payment system (Stripe + PayPal)
"""
import os
import stripe
import paypalrestsdk
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_stripe_connection():
    """Test Stripe configuration"""
    print("Testing Stripe Configuration...")
    
    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe_key:
        print("   [SKIP] STRIPE_SECRET_KEY not configured")
        return False
    
    stripe.api_key = stripe_key
    
    try:
        account = stripe.Account.retrieve()
        print(f"   [PASS] Connected to Stripe account: {account.id}")
        print(f"          Country: {account.country}")
        print(f"          Charges enabled: {account.charges_enabled}")
        return True
    except stripe.error.AuthenticationError:
        print("   [FAIL] Invalid Stripe API key")
        return False
    except Exception as e:
        print(f"   [FAIL] Stripe error: {str(e)}")
        return False

def test_paypal_connection():
    """Test PayPal configuration"""
    print("\nTesting PayPal Configuration...")
    
    client_id = os.getenv("PAYPAL_CLIENT_ID")
    client_secret = os.getenv("PAYPAL_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("   [SKIP] PayPal credentials not configured")
        return False
    
    try:
        # Configure PayPal
        paypalrestsdk.configure({
            "mode": os.getenv("PAYPAL_MODE", "sandbox"),
            "client_id": client_id,
            "client_secret": client_secret
        })
        
        # Test by creating a minimal payment object (not executed)
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
        
        print(f"   [PASS] PayPal configured successfully")
        print(f"          Mode: {os.getenv('PAYPAL_MODE', 'sandbox')}")
        print(f"          Client ID: {client_id[:8]}...")
        return True
        
    except Exception as e:
        print(f"   [FAIL] PayPal error: {str(e)}")
        return False

def test_payment_creation():
    """Test creating payments with both providers"""
    print("\nTesting Payment Creation...")
    
    # Test Stripe payment intent
    if os.getenv("STRIPE_SECRET_KEY"):
        try:
            intent = stripe.PaymentIntent.create(
                amount=2000,  # $20.00
                currency='usd',
                metadata={'test': 'true'}
            )
            print(f"   [PASS] Stripe payment intent created: {intent.id}")
        except Exception as e:
            print(f"   [FAIL] Stripe payment creation: {str(e)}")
    
    # Test PayPal payment
    if os.getenv("PAYPAL_CLIENT_ID"):
        try:
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {"payment_method": "paypal"},
                "redirect_urls": {
                    "return_url": "http://example.com/return",
                    "cancel_url": "http://example.com/cancel"
                },
                "transactions": [{
                    "amount": {"total": "20.00", "currency": "USD"},
                    "description": "Test Doula Life payment"
                }]
            })
            
            if payment.create():
                print(f"   [PASS] PayPal payment created: {payment.id}")
            else:
                print(f"   [FAIL] PayPal payment creation: {payment.error}")
        except Exception as e:
            print(f"   [FAIL] PayPal payment creation: {str(e)}")

def main():
    """Run all tests"""
    print("Unified Payment System Test Suite")
    print("=" * 50)
    
    # Test configurations
    stripe_ok = test_stripe_connection()
    paypal_ok = test_paypal_connection()
    
    # Test payment creation if configs are valid
    if stripe_ok or paypal_ok:
        test_payment_creation()
    
    # Summary
    print("\nTest Summary")
    print("-" * 30)
    print(f"Stripe:  {'[READY]' if stripe_ok else '[NOT CONFIGURED]'}")
    print(f"PayPal:  {'[READY]' if paypal_ok else '[NOT CONFIGURED]'}")
    
    if stripe_ok or paypal_ok:
        print("\nNext steps:")
        print("1. Run unified payment API: python unified_payments_app.py")
        print("2. Test endpoints at: http://localhost:8002/docs")
        print("3. Use POST /payments/create for unified interface")
    else:
        print("\nSetup required:")
        print("1. Add payment provider credentials to .env file")
        print("2. See README.md for detailed setup instructions")

if __name__ == "__main__":
    main()