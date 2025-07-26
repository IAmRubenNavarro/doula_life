import time
from jose import jwt, JWTError
import os

JWT_SECRET = os.getenv("JWT_SECRET",  default="supersecret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", default="HS256")

def sign_jwt(user_id: str) -> dict:
    payload = {
        "user_id": user_id,
        "expires": time.time() + 3600
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}

def decode_jwt(token: str):
    try: 
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if decoded["expires"] >= time.time():
            return decoded
    except JWTError:
        return None

