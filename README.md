# 🤱 Doula Life Backend API

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0+-00a393.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.13+-3776ab.svg?style=flat&logo=python&logoColor=white)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg?style=flat&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=flat&logo=supabase&logoColor=white)](https://supabase.com)

A robust, production-ready backend API for the Doula Life consulting and training platform. Built with **FastAPI**, **PostgreSQL**, and **Supabase** with comprehensive error handling, structured logging, and async support.

---

## ✨ Features

### 🏗️ **Core Architecture**
- **FastAPI** with async/await support for high performance
- **PostgreSQL** database via Supabase with connection pooling
- **Async SQLAlchemy** for efficient database operations
- **Pydantic** schemas for data validation and serialization

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
- **Database Connection Resilience** with retry policies (configurable)
- **Request/Response Logging** for audit trails
- **Error ID Tracking** for support and debugging
- **Startup/Shutdown Event Handling** for graceful lifecycle management

---

## 🏃‍♂️ Quick Start

### Prerequisites

- **Python 3.13+** (3.11+ supported)
- **Supabase Project** with PostgreSQL database
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

*More endpoints coming soon...*

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