# 🤱 Doula Life Backend API

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0+-00a393.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.13+-3776ab.svg?style=flat&logo=python&logoColor=white)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg?style=flat&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=flat&logo=supabase&logoColor=white)](https://supabase.com)
[![Stripe](https://img.shields.io/badge/Stripe-7.0.0-635BFF?style=flat&logo=stripe&logoColor=white)](https://stripe.com)
[![PayPal](https://img.shields.io/badge/PayPal-1.13.3-0070BA?style=flat&logo=paypal&logoColor=white)](https://paypal.com)

A robust, production-ready backend API for the Doula Life consulting and training platform. Built with **FastAPI**, **PostgreSQL**, **Supabase**, **Stripe**, and **PayPal** with comprehensive error handling, structured logging, and dual payment provider support.

---

## ✨ Features

### 🏗️ **Core Architecture**
- **FastAPI** with async/await support for high performance
- **PostgreSQL** database via Supabase with connection pooling
- **Async SQLAlchemy** for efficient database operations
- **Pydantic** schemas for data validation and serialization
- **Dual Payment Processing** with Stripe and PayPal integration

### 🛡️ **Enterprise-Grade Reliability**
- **Comprehensive Exception Handling** - Nothing fails silently
- **Structured Logging** with file rotation and error tracking
- **Database Transaction Management** with automatic rollbacks
- **Connection Pool Management** with health checks and timeouts
- **Global Error Handling** with user-friendly HTTP responses

### 🔧 **Developer Experience**
- **Detailed Documentation** with comprehensive docstrings
- **Health Check Endpoint** for monitoring and deployment
- **CORS Support** for frontend integration
- **Environment-based Configuration** for different deployment stages
- **Extensive Error Context** for debugging and monitoring

### 🚀 **Production Ready**
- **Database Connection Resilience** with automatic retry policies for transient failures
- **Smart Retry Logic** - Standard (3 attempts) and Critical (5 attempts) operation handling
- **Request/Response Logging** for audit trails
- **Error ID Tracking** for support and debugging
- **Startup/Shutdown Event Handling** for graceful lifecycle management

### 💳 **Payment Processing**
- **Dual Provider Support** - Stripe and PayPal integration
- **Unified Payment Interface** - Single endpoint for both providers
- **Stripe Payment Intents** for card and digital wallet payments
- **PayPal Orders** for PayPal account and credit card payments
- **Webhook Signature Verification** for payment status updates
- **Comprehensive Error Handling** for all payment scenarios
- **Metadata Tracking** for linking payments to services/appointments
- **PCI Compliance** through provider secure infrastructure

---

## 🏃‍♂️ Quick Start

### Prerequisites

- **Python 3.13+** (3.11+ supported)
- **Supabase Project** with PostgreSQL database
- **Stripe Account** for payment processing ([Get started](https://dashboard.stripe.com/register))
- **PayPal Developer Account** for PayPal payments ([Get started](https://developer.paypal.com/))
- **Git** for version control

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/doula_life_backend.git
cd doula_life_backend
```

2. **Create virtual environment**
```bash
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
# Includes: FastAPI, SQLAlchemy, Stripe, and all other dependencies
```

4. **Environment Configuration**
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration
# Required variables:
DATABASE_URL=postgresql+asyncpg://postgres:[password]@[project].supabase.co:5432/postgres
SECRET_KEY=your-secret-key-here
SUPABASE_URL=https://[project].supabase.co
SUPABASE_ANON_KEY=your-anon-key

# Stripe Configuration (Required for Stripe payments):
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# PayPal Configuration (Required for PayPal payments):
PAYPAL_CLIENT_ID=your_paypal_client_id
PAYPAL_CLIENT_SECRET=your_paypal_client_secret
PAYPAL_MODE=sandbox
PAYPAL_WEBHOOK_ID=your_paypal_webhook_id
```

5. **Run the application**
```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

6. **Verify installation**
```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs
```

---

## 📋 API Endpoints

### 🏥 **Health & Monitoring**
- `GET /health` - Service health check
- `GET /docs` - Interactive API documentation
- `GET /redoc` - Alternative API documentation

### 👥 **User Management**
- `POST /users/` - Create new user account
- `GET /users/{user_id}` - Get user by ID
- `GET /users/` - List users (paginated)

### 💳 **Payment Processing**

#### **Unified Payment Interface**
- `POST /payments/create-payment` - Create payment with any provider
- `GET /payments/` - List payment records (paginated)
- `GET /payments/{payment_id}` - Get payment by ID
- `PUT /payments/{payment_id}` - Update payment record

#### **Stripe Specific**
- `POST /payments/create-payment-intent` - Create Stripe payment intent
- `POST /payments/webhook` - Handle Stripe webhook events

#### **PayPal Specific**
- `POST /payments/paypal/create-order` - Create PayPal order
- `POST /payments/paypal/capture-payment/{payment_id}` - Capture PayPal payment
- `GET /payments/paypal/payment/{payment_id}` - Get PayPal payment details

### 📅 **Services & Appointments**
- `GET /services/` - List available services
- `POST /appointments/` - Book new appointment
- `GET /appointments/` - List user appointments

### 🎓 **Training Management**
- `GET /trainings/` - List available training programs
- `POST /training_enrollments/` - Enroll in training program

---

## 🗄️ Database Schema

### 👤 **Users**
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  first_name TEXT NOT NULL,
  middle_name TEXT,
  last_name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  role TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 🏥 **Services**
```sql
CREATE TABLE services (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT,
  description TEXT,
  service_type TEXT CHECK (service_type IN ('consulting', 'training')),
  price NUMERIC,
  duration_minutes INT,
  is_active BOOLEAN DEFAULT TRUE
);
```

### 📅 **Appointments**
```sql
CREATE TABLE appointments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  service_id UUID REFERENCES services(id) ON DELETE CASCADE,
  appointment_time TIMESTAMP WITH TIME ZONE NOT NULL,
  duration_minutes INT,
  state_id INT,
  notes TEXT,
  status TEXT DEFAULT 'scheduled',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 💳 **Payments**
```sql
CREATE TABLE payments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  amount NUMERIC NOT NULL,
  payment_method TEXT NOT NULL,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed')),
  stripe_payment_intent_id TEXT UNIQUE,
  stripe_customer_id TEXT,
  paypal_order_id TEXT UNIQUE,
  paypal_payment_id TEXT,
  paypal_payer_id TEXT,
  service_id UUID REFERENCES services(id),
  appointment_id UUID REFERENCES appointments(id),
  training_id UUID REFERENCES training(id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

*See `database/schema.sql` for complete schema*

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | ✅ | - |
| `SECRET_KEY` | JWT signing key | ✅ | - |
| `SUPABASE_URL` | Supabase project URL | ✅ | - |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | ✅ | - |
| `STRIPE_SECRET_KEY` | Stripe secret key for server-side operations | ⚠️ | - |
| `STRIPE_PUBLISHABLE_KEY` | Stripe publishable key for client-side | ⚠️ | - |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook endpoint secret | ⚠️ | - |
| `PAYPAL_CLIENT_ID` | PayPal application client ID | ⚠️ | - |
| `PAYPAL_CLIENT_SECRET` | PayPal application client secret | ⚠️ | - |
| `PAYPAL_MODE` | PayPal environment (sandbox/live) | ❌ | `sandbox` |
| `PAYPAL_WEBHOOK_ID` | PayPal webhook ID for verification | ⚠️ | - |
| `ENVIRONMENT` | Deployment environment | ❌ | `development` |
| `DEBUG` | Enable debug mode | ❌ | `True` |
| `OPENAI_API_KEY` | OpenAI API key (future use) | ❌ | - |

### Example `.env` file
```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@project.supabase.co:5432/postgres

# Security
SECRET_KEY=your-super-secret-key-change-in-production

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key

# Stripe Payment Processing
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# PayPal Payment Processing
PAYPAL_CLIENT_ID=your_paypal_client_id
PAYPAL_CLIENT_SECRET=your_paypal_client_secret
PAYPAL_MODE=sandbox
PAYPAL_WEBHOOK_ID=your_paypal_webhook_id

# Environment
ENVIRONMENT=development
DEBUG=true

# Optional: AI Features
OPENAI_API_KEY=sk-your-openai-key
```

---

## 📊 Logging & Monitoring

### Log Files
- **`logs/app.log`** - General application logs
- **`logs/errors.log`** - Error-only logs for monitoring

### Log Levels
- **DEBUG** - Detailed diagnostic information
- **INFO** - General application events
- **WARNING** - Potential issues that don't stop execution
- **ERROR** - Error events that may stop execution

### Error Tracking
Every error includes:
- **Unique Error ID** for tracking
- **Full Stack Trace** for debugging
- **Request Context** (method, URL, headers)
- **User Context** (when available)
- **Timestamp** and **Severity Level**

### Database Retry Policies
Automatic retry logic protects against transient database failures:

**Standard Retry Policy** (`@db_retry`):
- **3 attempts** total (1 initial + 2 retries)
- **Exponential backoff**: 1s, 2s, 4s (max 10s)
- Applied to: Read operations, queries, non-critical updates

**Critical Retry Policy** (`@db_retry_critical`):
- **5 attempts** total (1 initial + 4 retries)  
- **Aggressive backoff**: 0.5s, 1s, 2s, 4s, 8s, 16s (max 30s)
- Applied to: User creation, payment processing, appointment booking

**Smart Exception Handling**:
- Only retries connection/timeout errors (not data validation errors)
- Comprehensive logging of retry attempts for monitoring
- Automatic rollback on failure to maintain data integrity

**Active Protection**:
- ✅ User management operations (`app/crud/user.py`)
- ✅ Payment processing operations (`app/crud/payment.py`)
- ✅ Appointment management operations (`app/crud/appointment.py`)

---

## 🧪 Development

### Project Structure
```
doula_life_backend/
├── app/
│   ├── api/                 # API routes and endpoints
│   │   ├── users.py         # User management endpoints
│   │   └── routes.py        # Route configuration
│   ├── core/                # Core utilities and configuration
│   │   ├── config.py        # Application configuration
│   │   ├── exceptions.py    # Error handling utilities
│   │   └── logging_config.py # Logging configuration
│   ├── crud/                # Database operations
│   │   └── user.py          # User CRUD operations
│   ├── db/                  # Database configuration
│   │   └── session.py       # Database session management
│   ├── models/              # SQLAlchemy models
│   │   ├── user.py          # User model
│   │   ├── service.py       # Service model
│   │   └── appointment.py   # Appointment model
│   ├── schemas/             # Pydantic schemas
│   │   └── user.py          # User request/response schemas
│   └── main.py              # FastAPI application entry point
├── logs/                    # Application logs
├── .env                     # Environment configuration
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Code Quality
```bash
# Format code
black app/

# Sort imports
isort app/

# Type checking
mypy app/

# Lint code
flake8 app/
```

---

## 💳 Stripe Payment Integration

### Setup Guide

1. **Create Stripe Account**
   - Sign up at [https://dashboard.stripe.com/register](https://dashboard.stripe.com/register)
   - Complete account verification for live payments

2. **Get API Keys**
   ```bash
   # Navigate to: Developers → API Keys in Stripe Dashboard
   # Copy your keys to .env file:
   STRIPE_SECRET_KEY=sk_test_...        # For server-side operations
   STRIPE_PUBLISHABLE_KEY=pk_test_...   # For client-side integration
   ```

3. **Configure Webhooks**
   ```bash
   # In Stripe Dashboard: Developers → Webhooks
   # Create endpoint: https://yourdomain.com/payments/webhook
   # Select events: payment_intent.succeeded, payment_intent.payment_failed
   # Copy webhook secret to .env:
   STRIPE_WEBHOOK_SECRET=whsec_...
   ```

### Payment Flow

```python
# Example: Create payment intent
import requests

response = requests.post("http://localhost:8000/payments/create-payment-intent", 
    json={
        "amount": 2000,  # $20.00 in cents
        "currency": "usd",
        "user_id": "user-uuid",
        "service_id": "service-uuid"
    }
)

payment_intent = response.json()
# Use payment_intent["client_secret"] on frontend with Stripe.js
```

### Test Integration

```bash
# Test Stripe configuration
python test_stripe_simple.py

# Test API endpoints
curl -X POST http://localhost:8000/payments/create-payment-intent \
  -H "Content-Type: application/json" \
  -d '{"amount": 2000, "currency": "usd"}'
```

### Standalone Payment API

For testing without database dependencies:
```bash
# Run standalone Stripe API
python stripe_app.py
# or
uvicorn stripe_app:app --reload --port 8001

# Test at: http://localhost:8001/docs
```

### Security Features

- ✅ **Webhook signature verification** prevents unauthorized requests
- ✅ **Amount validation** prevents invalid payment amounts
- ✅ **Comprehensive error handling** for all Stripe scenarios
- ✅ **Metadata tracking** links payments to business entities
- ✅ **PCI compliance** through Stripe's secure infrastructure

---

## 💰 PayPal Payment Integration

### Setup Guide

1. **Create PayPal Developer Account**
   - Sign up at [https://developer.paypal.com/](https://developer.paypal.com/)
   - Create a new application in the PayPal Developer Dashboard

2. **Get API Credentials**
   ```bash
   # Navigate to: My Apps & Credentials in PayPal Developer Dashboard
   # Copy your credentials to .env file:
   PAYPAL_CLIENT_ID=your_paypal_client_id
   PAYPAL_CLIENT_SECRET=your_paypal_client_secret
   PAYPAL_MODE=sandbox  # or 'live' for production
   ```

3. **Configure Webhooks (Optional)**
   ```bash
   # In PayPal Developer Dashboard: Webhooks
   # Create webhook: https://yourdomain.com/payments/paypal/webhook
   # Select events: PAYMENT.SALE.COMPLETED, PAYMENT.SALE.DENIED
   # Copy webhook ID to .env:
   PAYPAL_WEBHOOK_ID=your_paypal_webhook_id
   ```

### Payment Flow

```python
# Example: Create unified payment (PayPal)
import requests

response = requests.post("http://localhost:8000/payments/create-payment", 
    json={
        "amount": 20.00,  # $20.00 in dollars
        "payment_provider": "paypal",
        "user_id": "user-uuid",
        "service_id": "service-uuid",
        "return_url": "https://yoursite.com/success",
        "cancel_url": "https://yoursite.com/cancel"
    }
)

payment_data = response.json()
# Redirect user to: payment_data["approval_url"]
# After approval, capture with payment_id and payer_id
```

### Unified Payment Interface

The unified endpoint supports both Stripe and PayPal:

```python
# Stripe Payment
{
    "amount": 20.00,
    "payment_provider": "stripe",
    "user_id": "123"
    # No URLs needed - returns client_secret for frontend
}

# PayPal Payment  
{
    "amount": 20.00,
    "payment_provider": "paypal", 
    "user_id": "123",
    "return_url": "https://yoursite.com/success",
    "cancel_url": "https://yoursite.com/cancel"
    # Returns approval_url for redirect
}
```

### Test Integration

```bash
# Test unified payment API
python unified_payments_app.py
# or
uvicorn unified_payments_app:app --reload --port 8002

# Test both providers
curl -X POST http://localhost:8002/payments/test

# Test at: http://localhost:8002/docs
```

### Key Differences: Stripe vs PayPal

| Feature | Stripe | PayPal |
|---------|---------|---------|
| **Amount Format** | Cents (2000 = $20.00) | Dollars (20.00 = $20.00) |
| **Client Integration** | Client-side with client_secret | Redirect to approval_url |
| **Payment Flow** | Single-step confirmation | Two-step (create → capture) |
| **Supported Methods** | Cards, Apple Pay, Google Pay | PayPal accounts, cards |
| **Webhook Events** | payment_intent.* | PAYMENT.SALE.* |

---

## 🚀 Deployment

### Docker Deployment
```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Considerations
- **Environment Variables** - Use secure secret management
- **Database Connections** - Configure connection pooling
- **Logging** - Set up log aggregation and monitoring
- **Health Checks** - Configure load balancer health checks
- **SSL/TLS** - Enable HTTPS in production
- **Rate Limiting** - Add API rate limiting middleware

---

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Development Guidelines
- **Write tests** for new features
- **Update documentation** for API changes
- **Follow code style** with Black and isort
- **Add logging** for important operations
- **Handle errors** with proper exception handling

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

- **Your Name** - *Initial work* - [@yourusername](https://github.com/yourusername)

---

## 🙏 Acknowledgments

- **FastAPI** - Amazing async web framework
- **Supabase** - Excellent PostgreSQL hosting
- **SQLAlchemy** - Powerful ORM for Python
- **Pydantic** - Data validation and settings management

---

## 📞 Support

- **Documentation**: [API Docs](http://localhost:8000/docs)
- **Issues**: [GitHub Issues](https://github.com/yourusername/doula_life_backend/issues)
- **Email**: your.email@example.com

---

*Built with ❤️ for the doula community*