from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class PaymentBase(BaseModel):
    user_id: UUID
    amount: float
    payment_method: str
    status: str = Field(..., pattern="^(pending|completed|failed)$")
    service_id: Optional[UUID] = None
    appointment_id: Optional[UUID] = None
    training_id: Optional[UUID] = None
    stripe_payment_intent_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    paypal_order_id: Optional[str] = None
    paypal_payment_id: Optional[str] = None
    paypal_payer_id: Optional[str] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(PaymentBase):
    pass

class PaymentInDB(PaymentBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class PaymentIntentCreate(BaseModel):
    amount: int  # Amount in cents
    currency: str = "usd"
    service_id: Optional[UUID] = None
    appointment_id: Optional[UUID] = None
    training_id: Optional[UUID] = None
    user_id: Optional[UUID] = None

class PaymentIntentResponse(BaseModel):
    client_secret: str
    payment_intent_id: str

class PayPalOrderCreate(BaseModel):
    amount: float  # Amount in dollars (not cents like Stripe)
    currency: str = "USD"
    service_id: Optional[UUID] = None
    appointment_id: Optional[UUID] = None
    training_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    return_url: str
    cancel_url: str

class PayPalOrderResponse(BaseModel):
    order_id: str
    approval_url: str
    status: str

class UnifiedPaymentCreate(BaseModel):
    amount: float  # Amount in dollars
    currency: str = "USD"
    payment_provider: str = Field(..., pattern="^(stripe|paypal)$")
    service_id: Optional[UUID] = None
    appointment_id: Optional[UUID] = None
    training_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    # PayPal-specific fields
    return_url: Optional[str] = None
    cancel_url: Optional[str] = None

class UnifiedPaymentResponse(BaseModel):
    provider: str
    payment_id: str
    client_secret: Optional[str] = None  # Stripe only
    approval_url: Optional[str] = None   # PayPal only
    status: str