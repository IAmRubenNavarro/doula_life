import os
from typing import Optional
from pydantic import BaseModel


class Settings(BaseModel):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg2://localhost:5432/doula_life")
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Supabase (if using)
    supabase_url: Optional[str] = os.getenv("SUPABASE_URL")
    supabase_key: Optional[str] = os.getenv("SUPABASE_ANON_KEY")
    
    # OpenAI (if using)
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Stripe
    stripe_secret_key: Optional[str] = os.getenv("STRIPE_SECRET_KEY")
    stripe_publishable_key: Optional[str] = os.getenv("STRIPE_PUBLISHABLE_KEY")
    stripe_webhook_secret: Optional[str] = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    # PayPal
    paypal_client_id: Optional[str] = os.getenv("PAYPAL_CLIENT_ID")
    paypal_client_secret: Optional[str] = os.getenv("PAYPAL_CLIENT_SECRET")
    paypal_mode: str = os.getenv("PAYPAL_MODE", "sandbox")  # sandbox or live
    paypal_webhook_id: Optional[str] = os.getenv("PAYPAL_WEBHOOK_ID")
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    

# Load environment variables from .env file if it exists
from dotenv import load_dotenv
load_dotenv()

settings = Settings()