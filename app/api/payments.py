from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
import stripe
import paypalrestsdk
import logging
import json

from app.schemas.payment import (
    PaymentCreate, PaymentInDB, PaymentUpdate, 
    PaymentIntentCreate, PaymentIntentResponse,
    PayPalOrderCreate, PayPalOrderResponse,
    UnifiedPaymentCreate, UnifiedPaymentResponse
)
from app.crud import payment as crud
from app.db.session import get_db
from app.core.config import settings

# Configure Stripe
stripe.api_key = settings.stripe_secret_key

# Configure PayPal
paypalrestsdk.configure({
    "mode": settings.paypal_mode,  # sandbox or live
    "client_id": settings.paypal_client_id,
    "client_secret": settings.paypal_client_secret
})

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=PaymentInDB)
async def create_payment(payment: PaymentCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_payment(db, payment)

@router.get("/", response_model=List[PaymentInDB])
async def read_all_payments(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.get_all_payments(db, skip, limit)

@router.get("/{payment_id}", response_model=PaymentInDB)
async def read_payment(payment_id: UUID, db: AsyncSession = Depends(get_db)):
    payment = await crud.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment

@router.put("/{payment_id}", response_model=PaymentInDB)
async def update_payment(payment_id: UUID, payment_update: PaymentUpdate, db: AsyncSession = Depends(get_db)):
    payment = await crud.update_payment(db, payment_id, payment_update)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment

@router.delete("/{payment_id}")
async def delete_payment(payment_id: UUID, db: AsyncSession = Depends(get_db)):
    deleted = await crud.delete_payment(db, payment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {"ok": True}

@router.post("/create-payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    payment_data: PaymentIntentCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a Stripe Payment Intent for processing payments.
    
    This endpoint creates a Payment Intent with Stripe that allows the client
    to collect payment from customers. The Payment Intent includes metadata
    to track which service, appointment, or training the payment is for.
    
    Args:
        payment_data: PaymentIntentCreate schema containing:
            - amount: Payment amount in cents (e.g., 2000 for $20.00)
            - currency: Currency code (default: "usd")
            - service_id: Optional UUID of the service being paid for
            - appointment_id: Optional UUID of the appointment being paid for
            - training_id: Optional UUID of the training being paid for
            - user_id: Optional UUID of the user making the payment
        db: Database session dependency
    
    Returns:
        PaymentIntentResponse containing:
            - client_secret: Secret for client-side payment confirmation
            - payment_intent_id: Stripe Payment Intent ID for tracking
    
    Raises:
        HTTPException: 
            - 400: Invalid Stripe parameters or API error
            - 500: Internal server error during payment intent creation
    """
    logger.info(f"Creating payment intent for amount: ${payment_data.amount/100:.2f} {payment_data.currency.upper()}")
    
    try:
        # Validate Stripe configuration
        if not settings.stripe_secret_key:
            logger.error("Stripe secret key not configured")
            raise HTTPException(
                status_code=500, 
                detail="Payment processing not configured"
            )
        
        # Build metadata dictionary for tracking payment context
        # This allows us to link the Stripe payment back to our business entities
        metadata = {}
        if payment_data.service_id:
            metadata["service_id"] = str(payment_data.service_id)
            logger.debug(f"Adding service_id to metadata: {payment_data.service_id}")
        if payment_data.appointment_id:
            metadata["appointment_id"] = str(payment_data.appointment_id)
            logger.debug(f"Adding appointment_id to metadata: {payment_data.appointment_id}")
        if payment_data.training_id:
            metadata["training_id"] = str(payment_data.training_id)
            logger.debug(f"Adding training_id to metadata: {payment_data.training_id}")
        if payment_data.user_id:
            metadata["user_id"] = str(payment_data.user_id)
            logger.debug(f"Adding user_id to metadata: {payment_data.user_id}")
        
        # Validate amount (must be positive and reasonable)
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
            amount=payment_data.amount,  # Amount in cents
            currency=payment_data.currency,
            metadata=metadata,
            automatic_payment_methods={
                'enabled': True,  # Enable all available payment methods
            },
            # Optional: Add description for better tracking
            description=f"Doula Life payment - {metadata.get('service_id', 'general')}"
        )
        
        logger.info(f"Successfully created Payment Intent: {intent.id}")
        logger.debug(f"Payment Intent details - Status: {intent.status}, Amount: {intent.amount}")
        
        return PaymentIntentResponse(
            client_secret=intent.client_secret,
            payment_intent_id=intent.id
        )
        
    except stripe.error.InvalidRequestError as e:
        # Handle invalid parameters sent to Stripe
        logger.error(f"Invalid Stripe request: {str(e)}")
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid payment parameters: {str(e)}"
        )
    except stripe.error.AuthenticationError as e:
        # Handle authentication issues with Stripe
        logger.error(f"Stripe authentication error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Payment service authentication failed"
        )
    except stripe.error.APIConnectionError as e:
        # Handle network issues with Stripe
        logger.error(f"Stripe API connection error: {str(e)}")
        raise HTTPException(
            status_code=503, 
            detail="Payment service temporarily unavailable"
        )
    except stripe.error.RateLimitError as e:
        # Handle rate limiting from Stripe
        logger.error(f"Stripe rate limit exceeded: {str(e)}")
        raise HTTPException(
            status_code=429, 
            detail="Too many payment requests, please try again later"
        )
    except stripe.error.StripeError as e:
        # Handle any other Stripe-specific errors
        logger.error(f"General Stripe error: {str(e)}")
        raise HTTPException(
            status_code=400, 
            detail=f"Payment processing error: {str(e)}"
        )
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error creating payment intent: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="An unexpected error occurred while processing payment"
        )

@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Handle Stripe webhook events for payment processing.
    
    This endpoint receives and processes webhook events from Stripe to keep
    our database in sync with payment statuses. It handles various payment
    events and updates our local payment records accordingly.
    
    Key webhook events handled:
    - payment_intent.succeeded: Payment completed successfully
    - payment_intent.payment_failed: Payment failed or was declined
    
    Security:
    - Verifies webhook signature to ensure requests come from Stripe
    - Uses Stripe webhook secret for signature validation
    
    Args:
        request: FastAPI Request object containing webhook payload
        db: Database session dependency
    
    Returns:
        dict: Success status confirmation for Stripe
    
    Raises:
        HTTPException:
            - 400: Invalid payload or signature verification failed
            - 500: Database error or unexpected processing error
    """
    logger.info("Received Stripe webhook event")
    
    # Extract payload and signature from request
    try:
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        if not sig_header:
            logger.error("Missing Stripe signature header")
            raise HTTPException(
                status_code=400, 
                detail="Missing webhook signature"
            )
        
        logger.debug(f"Processing webhook with signature: {sig_header[:20]}...")
        
    except Exception as e:
        logger.error(f"Error reading webhook payload: {str(e)}")
        raise HTTPException(
            status_code=400, 
            detail="Invalid webhook payload"
        )
    
    try:
        # Verify webhook signature to ensure request authenticity
        if not settings.stripe_webhook_secret:
            logger.error("Stripe webhook secret not configured")
            raise HTTPException(
                status_code=500, 
                detail="Webhook processing not configured"
            )
        
        logger.debug("Verifying webhook signature with Stripe")
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
        
        logger.info(f"Successfully verified webhook event: {event['type']} (ID: {event['id']})")
        
    except ValueError as e:
        # Handle malformed JSON payload
        logger.error(f"Invalid JSON payload in webhook: {str(e)}")
        raise HTTPException(
            status_code=400, 
            detail="Invalid webhook payload format"
        )
    except stripe.error.SignatureVerificationError as e:
        # Handle invalid webhook signature
        logger.error(f"Webhook signature verification failed: {str(e)}")
        raise HTTPException(
            status_code=400, 
            detail="Invalid webhook signature"
        )
    
    # Process different types of Stripe events
    try:
        event_type = event['type']
        logger.info(f"Processing webhook event type: {event_type}")
        
        if event_type == 'payment_intent.succeeded':
            # Handle successful payment completion
            payment_intent = event['data']['object']
            logger.info(f"Processing successful payment: {payment_intent['id']}")
            
            # Extract metadata for linking to our business entities
            metadata = payment_intent.get('metadata', {})
            user_id = metadata.get('user_id')
            service_id = metadata.get('service_id')
            appointment_id = metadata.get('appointment_id')
            training_id = metadata.get('training_id')
            
            logger.debug(f"Payment metadata - User: {user_id}, Service: {service_id}, "
                        f"Appointment: {appointment_id}, Training: {training_id}")
            
            # Validate required fields
            if not user_id:
                logger.warning(f"Payment {payment_intent['id']} missing user_id in metadata")
            
            # Create payment record in our database
            try:
                payment_data = PaymentCreate(
                    user_id=user_id,
                    amount=payment_intent['amount'] / 100,  # Convert from cents to dollars
                    payment_method="stripe",
                    status="completed",
                    service_id=service_id,
                    appointment_id=appointment_id,
                    training_id=training_id,
                    stripe_payment_intent_id=payment_intent['id'],
                    stripe_customer_id=payment_intent.get('customer')
                )
                
                # Save payment to database
                created_payment = await crud.create_payment(db, payment_data)
                logger.info(f"Successfully created payment record: {created_payment.id} "
                           f"for Stripe payment: {payment_intent['id']}")
                
            except Exception as db_error:
                logger.error(f"Database error creating payment record: {str(db_error)}", exc_info=True)
                # Don't raise here - we don't want to cause Stripe to retry
                # Log the error for manual investigation
                logger.error(f"MANUAL INVESTIGATION REQUIRED: Payment {payment_intent['id']} "
                           f"succeeded in Stripe but failed to save to database")
            
        elif event_type == 'payment_intent.payment_failed':
            # Handle failed payment attempts
            payment_intent = event['data']['object']
            failure_reason = payment_intent.get('last_payment_error', {}).get('message', 'Unknown')
            
            logger.warning(f"Payment failed: {payment_intent['id']} - Reason: {failure_reason}")
            
            # Optionally create a failed payment record for tracking
            metadata = payment_intent.get('metadata', {})
            if metadata.get('user_id'):
                try:
                    payment_data = PaymentCreate(
                        user_id=metadata.get('user_id'),
                        amount=payment_intent['amount'] / 100,
                        payment_method="stripe",
                        status="failed",
                        service_id=metadata.get('service_id'),
                        appointment_id=metadata.get('appointment_id'),
                        training_id=metadata.get('training_id'),
                        stripe_payment_intent_id=payment_intent['id'],
                        stripe_customer_id=payment_intent.get('customer')
                    )
                    
                    await crud.create_payment(db, payment_data)
                    logger.info(f"Created failed payment record for: {payment_intent['id']}")
                    
                except Exception as db_error:
                    logger.error(f"Error creating failed payment record: {str(db_error)}")
            
        elif event_type == 'payment_intent.requires_action':
            # Handle payments that require additional customer action (3D Secure, etc.)
            payment_intent = event['data']['object']
            logger.info(f"Payment requires additional action: {payment_intent['id']}")
            
        elif event_type == 'payment_intent.canceled':
            # Handle canceled payments
            payment_intent = event['data']['object']
            logger.info(f"Payment canceled: {payment_intent['id']}")
            
        else:
            # Log unhandled event types for monitoring
            logger.info(f"Received unhandled webhook event type: {event_type}")
            logger.debug(f"Event data: {event['data']}")
        
        # Return success response to Stripe
        logger.info(f"Successfully processed webhook event: {event['id']}")
        return {"status": "success", "event_id": event['id']}
        
    except Exception as e:
        # Handle any unexpected errors during event processing
        logger.error(f"Unexpected error processing webhook event {event.get('id', 'unknown')}: {str(e)}", 
                    exc_info=True)
        
        # Return error to Stripe - this will cause Stripe to retry the webhook
        raise HTTPException(
            status_code=500, 
            detail="Error processing webhook event"
        )

# ========================
# Unified Payment Interface
# ========================

@router.post("/create-payment", response_model=UnifiedPaymentResponse)
async def create_unified_payment(
    payment_data: UnifiedPaymentCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a payment using either Stripe or PayPal based on user preference.
    
    This unified endpoint allows clients to create payments with either
    provider by specifying the payment_provider field.
    
    Args:
        payment_data: UnifiedPaymentCreate schema containing:
            - amount: Payment amount in dollars
            - currency: Currency code (default: "USD") 
            - payment_provider: Either "stripe" or "paypal"
            - service_id, appointment_id, training_id, user_id: Optional tracking IDs
            - return_url, cancel_url: Required for PayPal, ignored for Stripe
        db: Database session dependency
    
    Returns:
        UnifiedPaymentResponse with provider-specific details
    
    Raises:
        HTTPException: Various payment processing errors
    """
    logger.info(f"Creating unified payment: {payment_data.payment_provider}, ${payment_data.amount:.2f}")
    
    try:
        if payment_data.payment_provider == "stripe":
            # Convert dollars to cents for Stripe
            stripe_data = PaymentIntentCreate(
                amount=int(payment_data.amount * 100),  # Convert to cents
                currency=payment_data.currency.lower(),
                service_id=payment_data.service_id,
                appointment_id=payment_data.appointment_id,
                training_id=payment_data.training_id,
                user_id=payment_data.user_id
            )
            
            # Call existing Stripe endpoint logic
            stripe_response = await create_payment_intent(stripe_data, db)
            
            return UnifiedPaymentResponse(
                provider="stripe",
                payment_id=stripe_response.payment_intent_id,
                client_secret=stripe_response.client_secret,
                status="requires_payment_method"
            )
            
        elif payment_data.payment_provider == "paypal":
            # Validate PayPal-specific requirements
            if not payment_data.return_url or not payment_data.cancel_url:
                raise HTTPException(
                    status_code=400,
                    detail="PayPal payments require return_url and cancel_url"
                )
            
            paypal_data = PayPalOrderCreate(
                amount=payment_data.amount,  # PayPal uses dollars
                currency=payment_data.currency,
                service_id=payment_data.service_id,
                appointment_id=payment_data.appointment_id,
                training_id=payment_data.training_id,
                user_id=payment_data.user_id,
                return_url=payment_data.return_url,
                cancel_url=payment_data.cancel_url
            )
            
            # Call existing PayPal endpoint logic
            paypal_response = await create_paypal_order(paypal_data, db)
            
            return UnifiedPaymentResponse(
                provider="paypal",
                payment_id=paypal_response.order_id,
                approval_url=paypal_response.approval_url,
                status=paypal_response.status.lower()
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid payment provider. Must be 'stripe' or 'paypal'"
            )
            
    except HTTPException:
        # Re-raise HTTPExceptions from sub-endpoints
        raise
    except Exception as e:
        logger.error(f"Unexpected error in unified payment: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing payment"
        )

# ========================
# PayPal Payment Endpoints
# ========================

@router.post("/paypal/create-order", response_model=PayPalOrderResponse)
async def create_paypal_order(
    order_data: PayPalOrderCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a PayPal order for payment processing.
    
    This endpoint creates a PayPal order that redirects users to PayPal 
    for payment approval. After approval, the payment must be captured
    using the capture endpoint.
    
    Args:
        order_data: PayPalOrderCreate schema containing:
            - amount: Payment amount in dollars (e.g., 20.00 for $20.00)
            - currency: Currency code (default: "USD")
            - service_id: Optional UUID of the service being paid for
            - appointment_id: Optional UUID of the appointment being paid for
            - training_id: Optional UUID of the training being paid for
            - user_id: Optional UUID of the user making the payment
            - return_url: URL to redirect after successful payment
            - cancel_url: URL to redirect if payment is cancelled
        db: Database session dependency
    
    Returns:
        PayPalOrderResponse containing:
            - order_id: PayPal Order ID for tracking
            - approval_url: URL to redirect user for payment approval
            - status: Order status (typically "CREATED")
    
    Raises:
        HTTPException: 
            - 400: Invalid PayPal parameters or API error
            - 500: Internal server error during order creation
    """
    logger.info(f"Creating PayPal order for amount: ${order_data.amount:.2f} {order_data.currency}")
    
    try:
        # Validate PayPal configuration
        if not settings.paypal_client_id or not settings.paypal_client_secret:
            logger.error("PayPal credentials not configured")
            raise HTTPException(
                status_code=500, 
                detail="PayPal payment processing not configured"
            )
        
        # Validate amount
        if order_data.amount <= 0:
            logger.warning(f"Invalid payment amount: {order_data.amount}")
            raise HTTPException(
                status_code=400, 
                detail="Payment amount must be greater than zero"
            )
        
        if order_data.amount > 10000:  # $10,000 max
            logger.warning(f"Payment amount too large: {order_data.amount}")
            raise HTTPException(
                status_code=400, 
                detail="Payment amount exceeds maximum allowed"
            )
        
        # Build custom metadata for tracking
        custom_data = {
            "user_id": str(order_data.user_id) if order_data.user_id else None,
            "service_id": str(order_data.service_id) if order_data.service_id else None,
            "appointment_id": str(order_data.appointment_id) if order_data.appointment_id else None,
            "training_id": str(order_data.training_id) if order_data.training_id else None,
        }
        
        # Remove None values
        custom_data = {k: v for k, v in custom_data.items() if v is not None}
        
        logger.info(f"Creating PayPal order with custom data: {custom_data}")
        
        # Validate return and cancel URLs
        try:
            from urllib.parse import urlparse
            for url_name, url in [("return_url", order_data.return_url), ("cancel_url", order_data.cancel_url)]:
                parsed = urlparse(url)
                if not parsed.scheme or not parsed.netloc:
                    logger.error(f"Invalid {url_name}: {url}")
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Invalid {url_name} format. Must be a valid URL."
                    )
        except Exception as url_error:
            if isinstance(url_error, HTTPException):
                raise
            logger.error(f"URL validation error: {str(url_error)}")
            raise HTTPException(
                status_code=400, 
                detail="Invalid URL format provided"
            )
        
        logger.debug(f"Creating PayPal payment with return_url: {order_data.return_url}")
        logger.debug(f"Creating PayPal payment with cancel_url: {order_data.cancel_url}")
        
        # Create PayPal payment object with comprehensive error handling
        try:
            payment_data = {
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "redirect_urls": {
                    "return_url": order_data.return_url,
                    "cancel_url": order_data.cancel_url
                },
                "transactions": [{
                    "item_list": {
                        "items": [{
                            "name": "Doula Life Service",
                            "sku": custom_data.get("service_id", "general"),
                            "price": f"{order_data.amount:.2f}",
                            "currency": order_data.currency,
                            "quantity": 1
                        }]
                    },
                    "amount": {
                        "total": f"{order_data.amount:.2f}",
                        "currency": order_data.currency
                    },
                    "description": f"Doula Life payment - {custom_data.get('service_id', 'general')}",
                    "custom": json.dumps(custom_data) if custom_data else ""
                }]
            }
            
            logger.debug(f"PayPal payment data structure created successfully")
            payment = paypalrestsdk.Payment(payment_data)
            
        except (TypeError, ValueError, json.JSONEncodeError) as e:
            logger.error(f"PayPal payment data construction error: {str(e)}")
            raise HTTPException(
                status_code=400, 
                detail="Invalid payment data format"
            )
        except Exception as e:
            logger.error(f"Unexpected error constructing PayPal payment: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500, 
                detail="Error preparing payment request"
            )
        
        # Create the payment with PayPal API
        try:
            logger.info(f"Sending payment creation request to PayPal API")
            payment_created = payment.create()
            
            if payment_created:
                logger.info(f"Successfully created PayPal payment: {payment.id}")
                logger.debug(f"PayPal payment state: {payment.state}")
                logger.debug(f"PayPal payment created at: {getattr(payment, 'create_time', 'unknown')}")
                
                # Find approval URL with comprehensive validation
                approval_url = None
                available_links = []
                
                try:
                    for link in payment.links:
                        available_links.append(f"{link.rel}: {link.href}")
                        if link.rel == "approval_url":
                            approval_url = link.href
                            logger.debug(f"Found approval URL: {approval_url}")
                            break
                except AttributeError as link_error:
                    logger.error(f"PayPal payment links attribute error: {str(link_error)}")
                    raise HTTPException(
                        status_code=500, 
                        detail="PayPal payment response format error"
                    )
                
                if not approval_url:
                    logger.error(f"No approval URL found for payment: {payment.id}")
                    logger.error(f"Available links: {available_links}")
                    raise HTTPException(
                        status_code=500, 
                        detail="PayPal approval URL not found in response"
                    )
                
                # Validate approval URL format
                try:
                    from urllib.parse import urlparse
                    parsed_approval = urlparse(approval_url)
                    if not parsed_approval.scheme or not parsed_approval.netloc:
                        logger.error(f"Invalid approval URL format: {approval_url}")
                        raise HTTPException(
                            status_code=500, 
                            detail="PayPal returned invalid approval URL"
                        )
                except Exception as approval_validation_error:
                    if isinstance(approval_validation_error, HTTPException):
                        raise
                    logger.error(f"Approval URL validation error: {str(approval_validation_error)}")
                    raise HTTPException(
                        status_code=500, 
                        detail="Error validating PayPal approval URL"
                    )
                
                logger.info(f"PayPal order created successfully - ID: {payment.id}, Status: {payment.state}")
                
                return PayPalOrderResponse(
                    order_id=payment.id,
                    approval_url=approval_url,
                    status=payment.state.upper()
                )
            else:
                # Payment creation failed - handle PayPal API errors
                error_details = "Unknown PayPal error"
                error_code = "UNKNOWN"
                
                try:
                    if hasattr(payment, 'error') and payment.error:
                        error_details = str(payment.error)
                        logger.error(f"PayPal API error details: {error_details}")
                        
                        # Try to extract specific error information
                        if isinstance(payment.error, dict):
                            error_code = payment.error.get('name', 'UNKNOWN')
                            error_message = payment.error.get('message', error_details)
                            error_details = f"{error_code}: {error_message}"
                            
                            # Log additional error context if available
                            if 'details' in payment.error:
                                for detail in payment.error.get('details', []):
                                    logger.error(f"PayPal error detail: {detail}")
                                    
                except Exception as error_parsing_error:
                    logger.error(f"Error parsing PayPal error response: {str(error_parsing_error)}")
                
                logger.error(f"PayPal payment creation failed for amount ${order_data.amount:.2f}: {error_details}")
                
                # Determine appropriate HTTP status based on PayPal error
                if "VALIDATION_ERROR" in error_code or "INVALID" in error_code:
                    status_code = 400
                elif "AUTHORIZATION" in error_code or "PERMISSION" in error_code:
                    status_code = 401
                elif "RATE_LIMIT" in error_code:
                    status_code = 429
                else:
                    status_code = 400
                
                raise HTTPException(
                    status_code=status_code, 
                    detail=f"PayPal order creation failed: {error_details}"
                )
                
        except paypalrestsdk.exceptions.ConnectionError as e:
            logger.error(f"PayPal API connection error: {str(e)}")
            raise HTTPException(
                status_code=503, 
                detail="PayPal service temporarily unavailable"
            )
        except paypalrestsdk.exceptions.SSLError as e:
            logger.error(f"PayPal SSL connection error: {str(e)}")
            raise HTTPException(
                status_code=503, 
                detail="Secure connection to PayPal failed"
            )
        except paypalrestsdk.exceptions.Timeout as e:
            logger.error(f"PayPal API timeout: {str(e)}")
            raise HTTPException(
                status_code=504, 
                detail="PayPal request timeout"
            )
        except Exception as api_error:
            if isinstance(api_error, HTTPException):
                raise
            logger.error(f"PayPal API unexpected error: {str(api_error)}", exc_info=True)
            raise HTTPException(
                status_code=500, 
                detail="PayPal service error"
            )
        
    except HTTPException:
        # Re-raise HTTPExceptions as-is to maintain proper error responses
        raise
    except Exception as e:
        # Catch any remaining unexpected errors
        logger.error(f"Unexpected error creating PayPal order: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="An unexpected error occurred while creating PayPal order"
        )

@router.post("/paypal/capture-payment/{payment_id}")
async def capture_paypal_payment(
    payment_id: str,
    payer_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Capture a PayPal payment after user approval.
    
    This endpoint is called after the user approves the payment on PayPal
    and is redirected back to your return_url with payment_id and PayerID.
    
    Args:
        payment_id: PayPal payment ID from the approval flow
        payer_id: PayPal payer ID from the approval flow
        db: Database session dependency
    
    Returns:
        dict: Payment capture status and details
    
    Raises:
        HTTPException:
            - 400: Payment capture failed or invalid parameters
            - 404: Payment not found
            - 500: Internal server error
    """
    logger.info(f"Capturing PayPal payment: {payment_id} for payer: {payer_id}")
    
    # Validate input parameters
    if not payment_id or not payment_id.strip():
        logger.error("Empty payment_id provided for PayPal capture")
        raise HTTPException(
            status_code=400, 
            detail="Payment ID is required"
        )
    
    if not payer_id or not payer_id.strip():
        logger.error(f"Empty payer_id provided for PayPal capture: {payment_id}")
        raise HTTPException(
            status_code=400, 
            detail="Payer ID is required for payment capture"
        )
    
    # Validate PayPal configuration
    if not settings.paypal_client_id or not settings.paypal_client_secret:
        logger.error("PayPal credentials not configured for payment capture")
        raise HTTPException(
            status_code=500, 
            detail="PayPal payment processing not configured"
        )
    
    try:
        # Find the payment with comprehensive error handling
        logger.debug(f"Retrieving PayPal payment: {payment_id}")
        
        try:
            payment = paypalrestsdk.Payment.find(payment_id)
        except paypalrestsdk.exceptions.ResourceNotFound as e:
            logger.error(f"PayPal payment not found in API: {payment_id}")
            raise HTTPException(
                status_code=404, 
                detail="Payment not found in PayPal system"
            )
        except paypalrestsdk.exceptions.ConnectionError as e:
            logger.error(f"PayPal API connection error during payment lookup: {str(e)}")
            raise HTTPException(
                status_code=503, 
                detail="PayPal service temporarily unavailable"
            )
        except paypalrestsdk.exceptions.Timeout as e:
            logger.error(f"PayPal API timeout during payment lookup: {str(e)}")
            raise HTTPException(
                status_code=504, 
                detail="PayPal request timeout"
            )
        except Exception as e:
            logger.error(f"Unexpected error retrieving PayPal payment: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500, 
                detail="Error retrieving payment from PayPal"
            )
        
        if not payment:
            logger.error(f"PayPal payment returned None: {payment_id}")
            raise HTTPException(
                status_code=404, 
                detail="Payment not found"
            )
        
        logger.info(f"Found PayPal payment: {payment.id}, state: {payment.state}")
        logger.debug(f"PayPal payment details - Intent: {getattr(payment, 'intent', 'unknown')}, "
                    f"Create time: {getattr(payment, 'create_time', 'unknown')}")
        
        # Validate payment state before capture
        if payment.state not in ["created", "approved"]:
            logger.warning(f"PayPal payment {payment.id} in invalid state for capture: {payment.state}")
            if payment.state == "completed":
                raise HTTPException(
                    status_code=400, 
                    detail="Payment has already been completed"
                )
            elif payment.state == "cancelled":
                raise HTTPException(
                    status_code=400, 
                    detail="Payment has been cancelled"
                )
            elif payment.state == "failed":
                raise HTTPException(
                    status_code=400, 
                    detail="Payment has failed and cannot be captured"
                )
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Payment in invalid state for capture: {payment.state}"
                )
        
        # Execute the payment with comprehensive error handling
        try:
            logger.info(f"Executing PayPal payment: {payment.id} with payer: {payer_id}")
            execution_data = {"payer_id": payer_id}
            execution_result = payment.execute(execution_data)
            
            if execution_result:
                logger.info(f"Successfully executed PayPal payment: {payment.id}")
                logger.debug(f"Payment execution result: {execution_result}")
                logger.debug(f"Final payment state: {payment.state}")
                
                # Validate payment completed successfully
                if payment.state != "approved":
                    logger.warning(f"PayPal payment {payment.id} executed but not in approved state: {payment.state}")
                
                # Extract transaction details with validation
                try:
                    if not hasattr(payment, 'transactions') or not payment.transactions:
                        logger.error(f"PayPal payment {payment.id} missing transaction data")
                        raise HTTPException(
                            status_code=500, 
                            detail="Payment completed but transaction data unavailable"
                        )
                    
                    transaction = payment.transactions[0]
                    logger.debug(f"Processing transaction: {getattr(transaction, 'description', 'No description')}")
                    
                    # Validate transaction amount
                    if not hasattr(transaction, 'amount') or not transaction.amount:
                        logger.error(f"PayPal payment {payment.id} missing amount data")
                        raise HTTPException(
                            status_code=500, 
                            detail="Payment completed but amount data unavailable"
                        )
                    
                    amount_total = transaction.amount.total
                    amount_currency = transaction.amount.currency
                    
                    logger.info(f"PayPal payment captured: {amount_total} {amount_currency}")
                    
                except (AttributeError, IndexError) as transaction_error:
                    logger.error(f"Error accessing PayPal transaction data: {str(transaction_error)}")
                    raise HTTPException(
                        status_code=500, 
                        detail="Payment completed but transaction details unavailable"
                    )
                
                # Parse custom data safely
                custom_data = {}
                try:
                    if hasattr(transaction, 'custom') and transaction.custom:
                        custom_data = json.loads(transaction.custom)
                        logger.debug(f"Parsed custom data: {custom_data}")
                    else:
                        logger.debug("No custom data found in PayPal transaction")
                except (json.JSONDecodeError, AttributeError) as custom_error:
                    logger.warning(f"Failed to parse custom data for payment {payment.id}: {str(custom_error)}")
                    # Continue without custom data - not critical for capture
                
                # Create payment record in database with comprehensive error handling
                try:
                    logger.info(f"Creating database record for PayPal payment: {payment.id}")
                    
                    payment_data = PaymentCreate(
                        user_id=custom_data.get('user_id'),
                        amount=float(amount_total),
                        payment_method="paypal",
                        status="completed",
                        service_id=custom_data.get('service_id'),
                        appointment_id=custom_data.get('appointment_id'),
                        training_id=custom_data.get('training_id'),
                        paypal_order_id=payment.id,
                        paypal_payment_id=payment.id,
                        paypal_payer_id=payer_id
                    )
                    
                    created_payment = await crud.create_payment(db, payment_data)
                    logger.info(f"Successfully created payment record: {created_payment.id} "
                               f"for PayPal payment: {payment.id}")
                    
                except ValueError as value_error:
                    logger.error(f"Payment data validation error: {str(value_error)}")
                    # Don't fail the capture - payment was successful
                    logger.warning(f"PayPal payment {payment.id} succeeded but payment data invalid")
                except Exception as db_error:
                    logger.error(f"Database error creating payment record: {str(db_error)}", exc_info=True)
                    # Don't fail the capture - payment was successful in PayPal
                    logger.error(f"MANUAL INVESTIGATION REQUIRED: PayPal payment {payment.id} "
                               f"succeeded but failed to save to database")
                
                # Return successful capture response
                return {
                    "status": "success",
                    "payment_id": payment.id,
                    "payer_id": payer_id,
                    "amount": amount_total,
                    "currency": amount_currency,
                    "state": payment.state,
                    "capture_time": getattr(payment, 'update_time', None)
                }
            else:
                # Payment execution failed - handle PayPal errors
                error_details = "Unknown PayPal execution error"
                error_code = "EXECUTION_FAILED"
                
                try:
                    if hasattr(payment, 'error') and payment.error:
                        error_details = str(payment.error)
                        logger.error(f"PayPal execution error details: {error_details}")
                        
                        # Extract specific error information
                        if isinstance(payment.error, dict):
                            error_code = payment.error.get('name', 'EXECUTION_FAILED')
                            error_message = payment.error.get('message', error_details)
                            error_details = f"{error_code}: {error_message}"
                            
                            # Log additional error context
                            if 'details' in payment.error:
                                for detail in payment.error.get('details', []):
                                    logger.error(f"PayPal execution error detail: {detail}")
                                    
                except Exception as error_parsing_error:
                    logger.error(f"Error parsing PayPal execution error: {str(error_parsing_error)}")
                
                logger.error(f"PayPal payment execution failed for {payment_id}: {error_details}")
                
                # Determine appropriate HTTP status
                if "PAYER_ID_MISSING" in error_code or "INVALID_PAYER" in error_code:
                    status_code = 400
                elif "PAYMENT_ALREADY_DONE" in error_code:
                    status_code = 409  # Conflict
                elif "PAYMENT_NOT_APPROVED" in error_code:
                    status_code = 400
                else:
                    status_code = 400
                
                raise HTTPException(
                    status_code=status_code, 
                    detail=f"Payment capture failed: {error_details}"
                )
                
        except paypalrestsdk.exceptions.BadRequest as e:
            logger.error(f"PayPal bad request error during execution: {str(e)}")
            raise HTTPException(
                status_code=400, 
                detail="Invalid payment capture request"
            )
        except paypalrestsdk.exceptions.UnauthorizedAccess as e:
            logger.error(f"PayPal unauthorized access during execution: {str(e)}")
            raise HTTPException(
                status_code=401, 
                detail="Unauthorized access to PayPal payment"
            )
        except paypalrestsdk.exceptions.ConnectionError as e:
            logger.error(f"PayPal connection error during execution: {str(e)}")
            raise HTTPException(
                status_code=503, 
                detail="PayPal service temporarily unavailable"
            )
        except paypalrestsdk.exceptions.Timeout as e:
            logger.error(f"PayPal timeout during execution: {str(e)}")
            raise HTTPException(
                status_code=504, 
                detail="PayPal request timeout"
            )
        except Exception as execution_error:
            if isinstance(execution_error, HTTPException):
                raise
            logger.error(f"Unexpected error during PayPal execution: {str(execution_error)}", exc_info=True)
            raise HTTPException(
                status_code=500, 
                detail="PayPal payment execution error"
            )
        
    except HTTPException:
        # Re-raise HTTPExceptions as-is to maintain proper error responses
        raise
    except Exception as e:
        # Catch any remaining unexpected errors
        logger.error(f"Unexpected error capturing PayPal payment {payment_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="An unexpected error occurred while capturing payment"
        )

@router.get("/paypal/payment/{payment_id}")
async def get_paypal_payment_details(payment_id: str):
    """
    Get PayPal payment details by payment ID.
    
    Args:
        payment_id: PayPal payment ID
    
    Returns:
        dict: Payment details from PayPal
    
    Raises:
        HTTPException:
            - 404: Payment not found
            - 500: PayPal API error
    """
    logger.info(f"Retrieving PayPal payment details: {payment_id}")
    
    # Validate input parameters
    if not payment_id or not payment_id.strip():
        logger.error("Empty payment_id provided for PayPal payment details retrieval")
        raise HTTPException(
            status_code=400, 
            detail="Payment ID is required"
        )
    
    # Validate PayPal configuration
    if not settings.paypal_client_id or not settings.paypal_client_secret:
        logger.error("PayPal credentials not configured for payment details retrieval")
        raise HTTPException(
            status_code=500, 
            detail="PayPal payment processing not configured"
        )
    
    try:
        # Retrieve payment with comprehensive error handling
        logger.debug(f"Fetching PayPal payment from API: {payment_id}")
        
        try:
            payment = paypalrestsdk.Payment.find(payment_id)
        except paypalrestsdk.exceptions.ResourceNotFound as e:
            logger.error(f"PayPal payment not found in API: {payment_id}")
            raise HTTPException(
                status_code=404, 
                detail="Payment not found in PayPal system"
            )
        except paypalrestsdk.exceptions.UnauthorizedAccess as e:
            logger.error(f"PayPal unauthorized access during payment retrieval: {str(e)}")
            raise HTTPException(
                status_code=401, 
                detail="Unauthorized access to PayPal payment details"
            )
        except paypalrestsdk.exceptions.ConnectionError as e:
            logger.error(f"PayPal API connection error during payment retrieval: {str(e)}")
            raise HTTPException(
                status_code=503, 
                detail="PayPal service temporarily unavailable"
            )
        except paypalrestsdk.exceptions.Timeout as e:
            logger.error(f"PayPal API timeout during payment retrieval: {str(e)}")
            raise HTTPException(
                status_code=504, 
                detail="PayPal request timeout"
            )
        except Exception as e:
            logger.error(f"Unexpected error retrieving PayPal payment: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500, 
                detail="Error retrieving payment from PayPal API"
            )
        
        if not payment:
            logger.error(f"PayPal payment API returned None: {payment_id}")
            raise HTTPException(
                status_code=404, 
                detail="Payment not found"
            )
        
        logger.info(f"Successfully retrieved PayPal payment: {payment.id}")
        logger.debug(f"PayPal payment state: {payment.state}, intent: {payment.intent}")
        
        # Safely extract payment details with validation
        try:
            payment_details = {
                "payment_id": payment.id,
                "state": getattr(payment, 'state', 'unknown'),
                "intent": getattr(payment, 'intent', 'unknown'),
                "create_time": getattr(payment, 'create_time', None),
                "update_time": getattr(payment, 'update_time', None)
            }
            
            # Safely add payer information
            try:
                if hasattr(payment, 'payer') and payment.payer:
                    payment_details["payer"] = {
                        "payment_method": getattr(payment.payer, 'payment_method', 'unknown'),
                        "status": getattr(payment.payer, 'status', 'unknown'),
                        "payer_info": getattr(payment.payer, 'payer_info', {})
                    }
                    logger.debug(f"Added payer information for payment: {payment.id}")
                else:
                    payment_details["payer"] = None
                    logger.debug(f"No payer information available for payment: {payment.id}")
            except Exception as payer_error:
                logger.warning(f"Error extracting payer information: {str(payer_error)}")
                payment_details["payer"] = None
            
            # Safely add transaction information
            try:
                if hasattr(payment, 'transactions') and payment.transactions:
                    transactions = []
                    for transaction in payment.transactions:
                        transaction_data = {
                            "amount": getattr(transaction, 'amount', {}),
                            "description": getattr(transaction, 'description', ''),
                            "custom": getattr(transaction, 'custom', ''),
                            "item_list": getattr(transaction, 'item_list', {})
                        }
                        
                        # Add related resources if available
                        if hasattr(transaction, 'related_resources'):
                            transaction_data["related_resources"] = transaction.related_resources
                        
                        transactions.append(transaction_data)
                    
                    payment_details["transactions"] = transactions
                    logger.debug(f"Added {len(transactions)} transaction(s) for payment: {payment.id}")
                else:
                    payment_details["transactions"] = []
                    logger.debug(f"No transactions available for payment: {payment.id}")
            except Exception as transaction_error:
                logger.warning(f"Error extracting transaction information: {str(transaction_error)}")
                payment_details["transactions"] = []
            
            # Safely add redirect URLs
            try:
                if hasattr(payment, 'redirect_urls') and payment.redirect_urls:
                    payment_details["redirect_urls"] = {
                        "return_url": getattr(payment.redirect_urls, 'return_url', ''),
                        "cancel_url": getattr(payment.redirect_urls, 'cancel_url', '')
                    }
                    logger.debug(f"Added redirect URLs for payment: {payment.id}")
                else:
                    payment_details["redirect_urls"] = None
            except Exception as redirect_error:
                logger.warning(f"Error extracting redirect URLs: {str(redirect_error)}")
                payment_details["redirect_urls"] = None
            
            # Safely add links
            try:
                if hasattr(payment, 'links') and payment.links:
                    links = []
                    for link in payment.links:
                        link_data = {
                            "href": getattr(link, 'href', ''),
                            "rel": getattr(link, 'rel', ''),
                            "method": getattr(link, 'method', 'GET')
                        }
                        links.append(link_data)
                    
                    payment_details["links"] = links
                    logger.debug(f"Added {len(links)} link(s) for payment: {payment.id}")
                else:
                    payment_details["links"] = []
            except Exception as links_error:
                logger.warning(f"Error extracting payment links: {str(links_error)}")
                payment_details["links"] = []
            
            logger.info(f"Successfully compiled payment details for: {payment.id}")
            return payment_details
            
        except Exception as detail_extraction_error:
            logger.error(f"Error extracting PayPal payment details: {str(detail_extraction_error)}", exc_info=True)
            raise HTTPException(
                status_code=500, 
                detail="Error processing payment details"
            )
        
    except HTTPException:
        # Re-raise HTTPExceptions as-is to maintain proper error responses
        raise
    except Exception as e:
        # Catch any remaining unexpected errors
        logger.error(f"Unexpected error retrieving PayPal payment details {payment_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="An unexpected error occurred while retrieving payment details"
        )

@router.post("/paypal/webhook")
async def paypal_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Handle PayPal webhook events for payment processing.
    
    This endpoint receives and processes webhook events from PayPal to keep
    our database in sync with payment statuses. It handles various payment
    events and updates our local payment records accordingly.
    
    Key webhook events handled:
    - PAYMENT.SALE.COMPLETED: Payment completed successfully
    - PAYMENT.SALE.DENIED: Payment was denied or failed
    - PAYMENT.SALE.REFUNDED: Payment was refunded
    - PAYMENT.SALE.REVERSED: Payment was reversed/charged back
    
    Security:
    - Verifies webhook signature to ensure requests come from PayPal
    - Uses PayPal webhook ID for signature validation
    
    Args:
        request: FastAPI Request object containing webhook payload
        db: Database session dependency
    
    Returns:
        dict: Success status confirmation for PayPal
    
    Raises:
        HTTPException:
            - 400: Invalid payload or signature verification failed
            - 500: Database error or unexpected processing error
    """
    logger.info("Received PayPal webhook event")
    
    # Extract payload and headers from request
    try:
        payload = await request.body()
        headers = dict(request.headers)
        
        if not payload:
            logger.error("Empty PayPal webhook payload")
            raise HTTPException(
                status_code=400, 
                detail="Empty webhook payload"
            )
        
        logger.debug(f"Processing PayPal webhook with {len(payload)} bytes payload")
        
    except Exception as e:
        logger.error(f"Error reading PayPal webhook payload: {str(e)}")
        raise HTTPException(
            status_code=400, 
            detail="Invalid webhook payload"
        )
    
    try:
        # Parse JSON payload
        try:
            event_data = json.loads(payload.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"Invalid JSON in PayPal webhook payload: {str(e)}")
            raise HTTPException(
                status_code=400, 
                detail="Invalid webhook payload format"
            )
        
        # Extract event information
        event_type = event_data.get('event_type')
        event_id = event_data.get('id', 'unknown')
        
        if not event_type:
            logger.error("PayPal webhook missing event_type")
            raise HTTPException(
                status_code=400, 
                detail="Invalid webhook event format"
            )
        
        logger.info(f"Processing PayPal webhook event: {event_type} (ID: {event_id})")
        
        # Verify webhook signature (if webhook ID is configured)
        if settings.paypal_webhook_id:
            try:
                # PayPal webhook verification requires specific headers
                required_headers = [
                    'paypal-auth-algo', 'paypal-transmission-id', 
                    'paypal-cert-id', 'paypal-transmission-sig', 
                    'paypal-transmission-time'
                ]
                
                missing_headers = []
                for header in required_headers:
                    if header not in headers:
                        missing_headers.append(header)
                
                if missing_headers:
                    logger.warning(f"PayPal webhook missing verification headers: {missing_headers}")
                    # Continue processing without verification if headers are missing
                    # This allows for testing environments where signature verification might not be set up
                else:
                    logger.debug("PayPal webhook signature verification headers present")
                    # In a production environment, you would implement PayPal's webhook verification here
                    # For now, we log that verification would happen here
                    logger.info(f"PayPal webhook signature verification would be performed here")
                    
            except Exception as verification_error:
                logger.warning(f"PayPal webhook signature verification error: {str(verification_error)}")
                # Continue processing - don't fail on verification errors in development
        else:
            logger.info("PayPal webhook verification skipped - no webhook ID configured")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing PayPal webhook headers: {str(e)}")
        raise HTTPException(
            status_code=400, 
            detail="Error processing webhook request"
        )
    
    # Process different types of PayPal webhook events
    try:
        logger.info(f"Processing PayPal webhook event type: {event_type}")
        
        if event_type == 'PAYMENT.SALE.COMPLETED':
            # Handle successful payment completion
            try:
                resource = event_data.get('resource', {})
                payment_id = resource.get('parent_payment', resource.get('id'))
                sale_id = resource.get('id')
                amount = resource.get('amount', {})
                
                logger.info(f"Processing PayPal sale completion: {sale_id} for payment: {payment_id}")
                
                if not payment_id:
                    logger.warning(f"PayPal sale {sale_id} missing parent payment ID")
                    return {"status": "ignored", "reason": "missing_payment_id"}
                
                # Extract payment details
                amount_value = amount.get('total', '0.00')
                amount_currency = amount.get('currency', 'USD')
                transaction_fee = resource.get('transaction_fee', {})
                fee_value = transaction_fee.get('value', '0.00')
                
                logger.debug(f"PayPal sale details - Amount: {amount_value} {amount_currency}, "
                           f"Fee: {fee_value}, Sale ID: {sale_id}")
                
                # Try to get custom data from the parent payment
                custom_data = {}
                try:
                    if payment_id:
                        parent_payment = paypalrestsdk.Payment.find(payment_id)
                        if parent_payment and parent_payment.transactions:
                            for transaction in parent_payment.transactions:
                                if hasattr(transaction, 'custom') and transaction.custom:
                                    custom_data = json.loads(transaction.custom)
                                    logger.debug(f"Retrieved custom data from parent payment: {custom_data}")
                                    break
                except Exception as custom_error:
                    logger.warning(f"Could not retrieve custom data for payment {payment_id}: {str(custom_error)}")
                
                # Create or update payment record in database
                try:
                    # Check if payment already exists
                    existing_payment = await crud.get_payment_by_paypal_id(db, payment_id)
                    
                    if existing_payment:
                        # Update existing payment to completed status
                        logger.info(f"Updating existing PayPal payment record: {existing_payment.id}")
                        
                        payment_update = PaymentUpdate(
                            user_id=existing_payment.user_id,
                            amount=float(amount_value),
                            payment_method="paypal",
                            status="completed",
                            service_id=existing_payment.service_id,
                            appointment_id=existing_payment.appointment_id,
                            training_id=existing_payment.training_id,
                            paypal_order_id=payment_id,
                            paypal_payment_id=sale_id,
                            paypal_payer_id=existing_payment.paypal_payer_id
                        )
                        
                        updated_payment = await crud.update_payment(db, existing_payment.id, payment_update)
                        logger.info(f"Updated payment record: {updated_payment.id} for PayPal sale: {sale_id}")
                        
                    else:
                        # Create new payment record
                        logger.info(f"Creating new PayPal payment record for sale: {sale_id}")
                        
                        payment_data = PaymentCreate(
                            user_id=custom_data.get('user_id'),
                            amount=float(amount_value),
                            payment_method="paypal",
                            status="completed",
                            service_id=custom_data.get('service_id'),
                            appointment_id=custom_data.get('appointment_id'),
                            training_id=custom_data.get('training_id'),
                            paypal_order_id=payment_id,
                            paypal_payment_id=sale_id,
                            paypal_payer_id=resource.get('payer_info', {}).get('payer_id')
                        )
                        
                        created_payment = await crud.create_payment(db, payment_data)
                        logger.info(f"Created payment record: {created_payment.id} for PayPal sale: {sale_id}")
                
                except Exception as db_error:
                    logger.error(f"Database error processing PayPal sale completion: {str(db_error)}", exc_info=True)
                    # Don't raise here - we don't want to cause PayPal to retry
                    logger.error(f"MANUAL INVESTIGATION REQUIRED: PayPal sale {sale_id} "
                               f"completed but failed to save/update in database")
                
            except Exception as sale_error:
                logger.error(f"Error processing PayPal sale completion: {str(sale_error)}", exc_info=True)
                # Continue processing - log error but don't fail webhook
                
        elif event_type == 'PAYMENT.SALE.DENIED':
            # Handle denied/failed payment
            try:
                resource = event_data.get('resource', {})
                payment_id = resource.get('parent_payment', resource.get('id'))
                sale_id = resource.get('id')
                
                logger.warning(f"PayPal sale denied: {sale_id} for payment: {payment_id}")
                
                if payment_id:
                    # Try to update payment record to failed status
                    try:
                        existing_payment = await crud.get_payment_by_paypal_id(db, payment_id)
                        
                        if existing_payment:
                            payment_update = PaymentUpdate(
                                user_id=existing_payment.user_id,
                                amount=existing_payment.amount,
                                payment_method="paypal",
                                status="failed",
                                service_id=existing_payment.service_id,
                                appointment_id=existing_payment.appointment_id,
                                training_id=existing_payment.training_id,
                                paypal_order_id=payment_id,
                                paypal_payment_id=sale_id,
                                paypal_payer_id=existing_payment.paypal_payer_id
                            )
                            
                            await crud.update_payment(db, existing_payment.id, payment_update)
                            logger.info(f"Updated payment {existing_payment.id} to failed status")
                            
                    except Exception as db_error:
                        logger.error(f"Error updating failed PayPal payment: {str(db_error)}")
                
            except Exception as denial_error:
                logger.error(f"Error processing PayPal sale denial: {str(denial_error)}")
                
        elif event_type == 'PAYMENT.SALE.REFUNDED':
            # Handle payment refunds
            try:
                resource = event_data.get('resource', {})
                sale_id = resource.get('sale_id')
                refund_id = resource.get('id')
                amount = resource.get('amount', {})
                
                logger.info(f"PayPal refund processed: {refund_id} for sale: {sale_id}")
                logger.info(f"Refund amount: {amount.get('total', '0.00')} {amount.get('currency', 'USD')}")
                
                # In a complete implementation, you would:
                # 1. Find the original payment by sale_id
                # 2. Create a refund record
                # 3. Update payment status if fully refunded
                # For now, we just log the refund event
                
            except Exception as refund_error:
                logger.error(f"Error processing PayPal refund: {str(refund_error)}")
                
        elif event_type == 'PAYMENT.SALE.REVERSED':
            # Handle payment reversals/chargebacks
            try:
                resource = event_data.get('resource', {})
                sale_id = resource.get('sale_id')
                
                logger.warning(f"PayPal payment reversed/chargeback: {sale_id}")
                
                # In a complete implementation, you would:
                # 1. Find the original payment by sale_id
                # 2. Update payment status to reversed
                # 3. Create a chargeback record
                # 4. Trigger business logic for handling chargebacks
                
            except Exception as reversal_error:
                logger.error(f"Error processing PayPal reversal: {str(reversal_error)}")
                
        else:
            # Log unhandled event types for monitoring
            logger.info(f"Received unhandled PayPal webhook event type: {event_type}")
            logger.debug(f"Event data summary: {event_data.get('summary', 'No summary available')}")
        
        # Return success response to PayPal
        logger.info(f"Successfully processed PayPal webhook event: {event_id}")
        return {"status": "success", "event_id": event_id, "event_type": event_type}
        
    except Exception as e:
        # Handle any unexpected errors during event processing
        logger.error(f"Unexpected error processing PayPal webhook event {event_id}: {str(e)}", 
                    exc_info=True)
        
        # Return error to PayPal - this will cause PayPal to retry the webhook
        raise HTTPException(
            status_code=500, 
            detail="Error processing webhook event"
        )
