# 🔌 Database-API Integration Guide

## FastAPI Model Mapping

This guide shows how your database schema maps to your FastAPI application models.

### 🗄️ **Database → Python Model Mapping**

#### **Users Table**
```sql
-- Database
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  role TEXT NOT NULL CHECK (role IN (...)),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

```python
# Python Model (app/models/user.py)
class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
```

#### **Payments Table**
```sql
-- Database (with all payment provider fields)
CREATE TABLE payments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  amount NUMERIC(10,2) NOT NULL CHECK (amount > 0),
  currency TEXT DEFAULT 'USD' NOT NULL,
  payment_method TEXT NOT NULL,
  status TEXT DEFAULT 'pending' NOT NULL,
  
  -- Stripe fields
  stripe_payment_intent_id TEXT UNIQUE,
  stripe_customer_id TEXT,
  stripe_charge_id TEXT,
  
  -- PayPal fields
  paypal_order_id TEXT UNIQUE,
  paypal_payment_id TEXT,
  paypal_payer_id TEXT,
  
  metadata JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

```python
# Python Model (app/models/payment.py) 
class Payment(Base):
    __tablename__ = "payments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    amount = Column(Numeric(10,2), nullable=False)
    currency = Column(String, default="USD", nullable=False)
    payment_method = Column(String, nullable=False)
    status = Column(String, default="pending", nullable=False)
    
    # Provider-specific fields
    stripe_payment_intent_id = Column(String, unique=True)
    stripe_customer_id = Column(String)
    stripe_charge_id = Column(String)
    paypal_order_id = Column(String, unique=True)
    paypal_payment_id = Column(String)
    paypal_payer_id = Column(String)
    
    metadata = Column(JSON)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
```

### 📋 **Pydantic Schemas**

#### **Payment Schemas**
```python
# app/schemas/payment.py
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class PaymentBase(BaseModel):
    amount: float = Field(..., gt=0, description="Payment amount in dollars")
    currency: str = Field(default="USD", regex="^[A-Z]{3}$")
    payment_method: str = Field(..., regex="^(stripe|paypal|cash|check|bank_transfer)$")
    status: str = Field(default="pending", regex="^(pending|completed|failed|refunded)$")

class PaymentCreate(PaymentBase):
    user_id: UUID
    service_id: Optional[UUID] = None
    appointment_id: Optional[UUID] = None
    training_id: Optional[UUID] = None

class PaymentInDB(PaymentBase):
    id: UUID
    user_id: UUID
    stripe_payment_intent_id: Optional[str] = None
    paypal_order_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### 🔄 **CRUD Operations**

#### **Database Query Examples**
```python
# app/crud/payment.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

async def get_payment_by_stripe_id(db: AsyncSession, stripe_payment_intent_id: str):
    """Get payment by Stripe Payment Intent ID"""
    result = await db.execute(
        select(Payment).where(Payment.stripe_payment_intent_id == stripe_payment_intent_id)
    )
    return result.scalar_one_or_none()

async def get_user_payments(db: AsyncSession, user_id: UUID, status: Optional[str] = None):
    """Get all payments for a user, optionally filtered by status"""
    query = select(Payment).where(Payment.user_id == user_id)
    if status:
        query = query.where(Payment.status == status)
    result = await db.execute(query)
    return result.scalars().all()

async def create_payment(db: AsyncSession, payment_in: PaymentCreate):
    """Create new payment record"""
    payment = Payment(**payment_in.model_dump())
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment
```

### 🎯 **API Endpoint Integration**

#### **Payment Endpoints**
```python
# app/api/payments.py
@router.post("/", response_model=PaymentInDB)
async def create_payment(
    payment: PaymentCreate, 
    db: AsyncSession = Depends(get_db)
):
    """Create new payment record"""
    return await crud.create_payment(db, payment)

@router.get("/{payment_id}", response_model=PaymentInDB)
async def get_payment(
    payment_id: UUID, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get payment by ID (user can only see their own)"""
    payment = await crud.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # RLS will handle access control, but double-check
    if payment.user_id != current_user.id and current_user.role not in ['administrator', 'owner']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return payment
```

### 🔐 **Row Level Security Integration**

#### **Database RLS + FastAPI Auth**
```python
# app/core/auth.py
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    """Get current authenticated user"""
    # Verify JWT token
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user_id: str = payload.get("sub")
    
    # Set Supabase auth context for RLS
    await db.execute(text("SELECT set_config('request.jwt.claim.sub', :user_id, true)"), 
                     {"user_id": user_id})
    
    # Get user from database (RLS will ensure proper access)
    user = await crud.get_user(db, UUID(user_id))
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    
    return user
```

### 🔄 **Webhook Integration**

#### **Stripe Webhook → Database**
```python
# app/api/payments.py
@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle Stripe webhook events"""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    # Verify webhook signature
    event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        
        # Find existing payment record
        payment = await crud.get_payment_by_stripe_id(db, payment_intent['id'])
        
        if payment:
            # Update payment status
            payment_update = PaymentUpdate(
                status="completed",
                payment_date=datetime.now()
            )
            await crud.update_payment(db, payment.id, payment_update)
            
            # Create audit record
            audit_data = PaymentAuditCreate(
                payment_id=payment.id,
                old_status=payment.status,
                new_status="completed",
                change_reason="stripe_webhook",
                provider_data=payment_intent
            )
            await crud.create_payment_audit(db, audit_data)
```

### 📊 **Database Views → API Responses**

#### **Payment Summary View**
```sql
-- Database View
CREATE VIEW payment_summary AS
SELECT 
  payment_method,
  status,
  COUNT(*) as payment_count,
  SUM(amount) as total_amount
FROM payments 
GROUP BY payment_method, status;
```

```python
# API Endpoint
@router.get("/summary", response_model=List[PaymentSummary])
async def get_payment_summary(db: AsyncSession = Depends(get_db)):
    """Get payment summary statistics"""
    result = await db.execute(text("SELECT * FROM payment_summary"))
    return [PaymentSummary(**row._asdict()) for row in result.fetchall()]
```

### 🧪 **Testing Database Integration**

#### **Test Database Setup**
```python
# tests/conftest.py
@pytest.fixture
async def test_db():
    """Create test database session"""
    engine = create_async_engine("postgresql+asyncpg://test:test@localhost/test_db")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = AsyncSession(engine)
    yield async_session
    await async_session.close()

@pytest.fixture
async def test_user(test_db):
    """Create test user"""
    user_data = UserCreate(
        first_name="Test",
        last_name="User", 
        email="test@example.com",
        role="individual_client"
    )
    return await crud.create_user(test_db, user_data)
```

#### **Payment Integration Tests**
```python
# tests/test_payments.py
async def test_create_payment(test_db, test_user):
    """Test payment creation"""
    payment_data = PaymentCreate(
        user_id=test_user.id,
        amount=100.00,
        currency="USD",
        payment_method="stripe",
        status="pending"
    )
    
    payment = await crud.create_payment(test_db, payment_data)
    assert payment.amount == 100.00
    assert payment.user_id == test_user.id
    assert payment.status == "pending"

async def test_stripe_webhook_processing(test_db, test_user):
    """Test Stripe webhook creates audit record"""
    # Create initial payment
    payment = await crud.create_payment(test_db, PaymentCreate(...))
    
    # Simulate webhook updating payment
    webhook_data = {"id": "pi_test123", "status": "succeeded"}
    
    # Process webhook (this would be in your webhook handler)
    updated_payment = await crud.update_payment_status(test_db, payment.id, "completed")
    
    # Verify audit record was created
    audit_records = await crud.get_payment_audit(test_db, payment.id)
    assert len(audit_records) == 1
    assert audit_records[0].new_status == "completed"
```

### 🔧 **Environment Configuration**

#### **Database Connection Setup**
```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str
    
    # Payment Providers
    stripe_secret_key: Optional[str] = None
    paypal_client_id: Optional[str] = None
    
    class Config:
        env_file = ".env"

settings = Settings()

# app/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine(settings.database_url)

async def get_db():
    async with AsyncSession(engine) as session:
        yield session
```

This integration ensures your FastAPI application works seamlessly with your database schema while maintaining security and performance! 🚀