from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.status import HTTP_403_FORBIDDEN
from pydantic import BaseModel
from app.auth.jwt_handler import sign_jwt
from app.auth.jwt_handler import decode_jwt

router = APIRouter()
security = HTTPBearer()

fake_user_db = {
    "test@example.com": {
        "email": "test@example.com",
        "password": "password123"
    }
}

class LoginRequest(BaseModel):
    email: str
    password: str

def authorize(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    decoded_token = decode_jwt(token)
    if decoded_token is None:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Invalid token or expired token")
    return decoded_token

@router.post("/login")
def login_user(user: LoginRequest):
    user_data = fake_user_db.get(user.email)
    if not user_data or user_data["password"] != user.password:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Invalid email or password")
    
    return sign_jwt(user.email)

@router.get("/protected")
def protected_route(user=Depends(authorize)):
    return {"message": "Access granted", "user": user}