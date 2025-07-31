"""
Comprehensive test script to verify Stripe integration
Run this after setting up your environment variables

This script tests:
1. Environment variable configuration
2. Stripe API connectivity and authentication
3. Payment intent creation
4. Error handling scenarios

Usage:
    python test_stripe.py

Requirements:
    - .env file with STRIPE_SECRET_KEY configured
    - stripe package installed (pip install stripe)
"""
import os
import stripe
import logging
from dotenv import load_dotenv
from typing import Optional

# Configure logging for better test output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

def check_environment_variables() -> bool:
    """
    Check if all required Stripe environment variables are configured.
    
    Returns:
        bool: True if all required variables are present, False otherwise
    """
    print("Checking environment variables...")
    
    required_vars = {
        'STRIPE_SECRET_KEY': 'Secret key for server-side Stripe operations',
        'STRIPE_PUBLISHABLE_KEY': 'Publishable key for client-side integration',
        'STRIPE_WEBHOOK_SECRET': 'Webhook secret for signature verification'
    }
    
    missing_vars = []
    
    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if value:
            # Mask the key for security (show first 8 and last 4 characters)
            if len(value) > 12:
                masked_value = f"{value[:8]}...{value[-4:]}"
            else:
                masked_value = "***"
            print(f"   [PASS] {var_name}: {masked_value}")
        else:
            print(f"   [FAIL] {var_name}: Not configured - {description}")
            missing_vars.append(var_name)
    
    if missing_vars:
        print(f"\n[FAIL] Missing {len(missing_vars)} required environment variable(s)")
        return False
    
    print("[PASS] All environment variables configured")
    return True

def test_stripe_connection() -> bool:
    """
    Test basic Stripe API connection and authentication.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    print("\nTesting Stripe API connection...")
    
    # Configure Stripe with secret key
    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe_key:
        logger.error("STRIPE_SECRET_KEY not found in environment variables")
        print("[FAIL] Cannot test connection without STRIPE_SECRET_KEY")
        return False
    
    stripe.api_key = stripe_key
    
    try:
        logger.info("Attempting to retrieve Stripe account information")
        
        # Test API connection by retrieving account info
        account = stripe.Account.retrieve()
        
        print(f"✅ Successfully connected to Stripe!")
        print(f"   Account ID: {account.id}")
        print(f"   Business name: {account.business_profile.get('name', 'N/A')}")
        print(f"   Country: {account.country}")
        print(f"   Account type: {account.type}")
        
        # Check if account can accept payments
        if account.charges_enabled:
            print("   ✅ Account can accept charges")
        else:
            print("   ⚠️  Account cannot accept charges yet")
        
        if account.payouts_enabled:
            print("   ✅ Account can receive payouts")
        else:
            print("   ⚠️  Account cannot receive payouts yet")
        
        logger.info(f"Connected to Stripe account: {account.id}")
        return True
        
    except stripe.error.AuthenticationError as e:
        logger.error(f"Authentication failed: {str(e)}")
        print("❌ Authentication failed - Invalid Stripe API key")
        print("   Please check your STRIPE_SECRET_KEY in the .env file")
        return False
        
    except stripe.error.APIConnectionError as e:
        logger.error(f"Network connection failed: {str(e)}")
        print("❌ Network connection failed")
        print("   Please check your internet connection")
        return False
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe API error: {str(e)}")
        print(f"❌ Stripe API error: {str(e)}")
        return False
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        print(f"❌ Unexpected error connecting to Stripe: {str(e)}")
        return False

def test_create_payment_intent() -> bool:
    """
    Test creating a Stripe Payment Intent.
    
    Returns:
        bool: True if payment intent created successfully, False otherwise
    """
    print("\n💳 Testing Payment Intent creation...")
    
    try:
        logger.info("Creating test payment intent")
        
        # Create a test payment intent
        intent = stripe.PaymentIntent.create(
            amount=2000,  # $20.00 in cents
            currency='usd',
            metadata={
                'test': 'true',
                'service_id': 'test-service-123',
                'user_id': 'test-user-456',
                'environment': 'test'
            },
            description="Test payment intent from test script"
        )
        
        print(f"✅ Successfully created payment intent!")
        print(f"   Payment Intent ID: {intent.id}")
        print(f"   Amount: ${intent.amount / 100:.2f} {intent.currency.upper()}")
        print(f"   Status: {intent.status}")
        print(f"   Client Secret: {intent.client_secret[:20]}...")
        
        # Check payment methods
        if intent.automatic_payment_methods and intent.automatic_payment_methods.enabled:
            print("   ✅ Automatic payment methods enabled")
        
        logger.info(f"Created payment intent: {intent.id}")
        
        # Test retrieving the payment intent
        try:
            retrieved_intent = stripe.PaymentIntent.retrieve(intent.id)
            print(f"   ✅ Successfully retrieved payment intent: {retrieved_intent.id}")
            logger.info(f"Retrieved payment intent: {retrieved_intent.id}")
        except Exception as retrieve_error:
            logger.warning(f"Could not retrieve payment intent: {str(retrieve_error)}")
            print(f"   ⚠️  Could not retrieve payment intent: {str(retrieve_error)}")
        
        return True
        
    except stripe.error.InvalidRequestError as e:
        logger.error(f"Invalid request parameters: {str(e)}")
        print(f"❌ Invalid request parameters: {str(e)}")
        return False
        
    except stripe.error.AuthenticationError as e:
        logger.error(f"Authentication error: {str(e)}")
        print("❌ Authentication error - check your API key")
        return False
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        print(f"❌ Stripe error: {str(e)}")
        return False
        
    except Exception as e:
        logger.error(f"Unexpected error creating payment intent: {str(e)}", exc_info=True)
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_webhook_signature_validation() -> bool:
    """
    Test webhook signature validation setup.
    
    Returns:
        bool: True if webhook secret is configured, False otherwise
    """
    print("\n🔐 Testing webhook configuration...")
    
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    if not webhook_secret:
        print("❌ STRIPE_WEBHOOK_SECRET not configured")
        print("   This is required for webhook signature verification")
        return False
    
    if not webhook_secret.startswith("whsec_"):
        print("❌ STRIPE_WEBHOOK_SECRET appears to be invalid")
        print("   Webhook secrets should start with 'whsec_'")
        return False
    
    print("✅ Webhook secret configured correctly")
    print(f"   Secret: {webhook_secret[:10]}...")
    return True

def run_all_tests() -> None:
    """
    Run all Stripe integration tests in sequence.
    
    This function orchestrates the complete test suite, providing
    a summary of results and actionable next steps.
    """
    print("Doula Life Backend - Stripe Integration Test Suite")
    print("=" * 60)
    
    # Track test results
    test_results = {
        'environment': False,
        'connection': False,
        'payment_intent': False,
        'webhook': False
    }
    
    try:
        # Test 1: Environment Variables
        logger.info("Starting environment variable checks")
        test_results['environment'] = check_environment_variables()
        
        # Test 2: Stripe Connection (only if environment is OK)
        if test_results['environment']:
            logger.info("Starting Stripe connection test")
            test_results['connection'] = test_stripe_connection()
            
            # Test 3: Payment Intent Creation (only if connection is OK)
            if test_results['connection']:
                logger.info("Starting payment intent test")
                test_results['payment_intent'] = test_create_payment_intent()
        
        # Test 4: Webhook Configuration (independent test)
        logger.info("Starting webhook configuration test")
        test_results['webhook'] = test_webhook_signature_validation()
        
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        logger.info("Test suite interrupted by user")
        return
    except Exception as e:
        print(f"\n❌ Unexpected error during test execution: {str(e)}")
        logger.error(f"Unexpected error in test suite: {str(e)}", exc_info=True)
        return
    
    # Print test summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name.replace('_', ' ').title():<20} {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    # Provide actionable next steps
    print("\n📝 NEXT STEPS:")
    print("-" * 60)
    
    if not test_results['environment']:
        print("1. 🔧 Configure environment variables in your .env file:")
        print("   STRIPE_SECRET_KEY=sk_test_...")
        print("   STRIPE_PUBLISHABLE_KEY=pk_test_...")
        print("   STRIPE_WEBHOOK_SECRET=whsec_...")
        print("   (Get these from your Stripe Dashboard)")
        
    elif not test_results['connection']:
        print("1. 🔑 Check your Stripe API keys:")
        print("   - Verify STRIPE_SECRET_KEY is correct")
        print("   - Ensure you're using test keys for development")
        print("   - Check your Stripe account status")
        
    elif not test_results['payment_intent']:
        print("1. ⚠️  Payment Intent creation failed:")
        print("   - Check the error messages above")
        print("   - Verify your Stripe account can create payments")
        print("   - Contact Stripe support if issues persist")
        
    else:
        print("1. ✅ All core tests passed! You can now:")
        print("   - Install dependencies: pip install -r requirements.txt")
        print("   - Run your FastAPI app: uvicorn app.main:app --reload")
        print("   - Test the payment endpoints at http://localhost:8000/docs")
    
    if not test_results['webhook']:
        print("2. 🔐 Configure webhook secret for production:")
        print("   - Create webhook endpoint in Stripe Dashboard")
        print("   - Point it to: https://yourdomain.com/payments/webhook")
        print("   - Copy the webhook secret to STRIPE_WEBHOOK_SECRET")
    
    print("\n3. 📚 Additional resources:")
    print("   - Stripe API docs: https://stripe.com/docs/api")
    print("   - Stripe webhook guide: https://stripe.com/docs/webhooks")
    print("   - FastAPI docs: https://fastapi.tiangolo.com/")
    
    # Log final summary
    if passed_tests == total_tests:
        logger.info("All tests passed successfully")
    else:
        logger.warning(f"Only {passed_tests}/{total_tests} tests passed")

if __name__ == "__main__":
    # Run the complete test suite
    run_all_tests()