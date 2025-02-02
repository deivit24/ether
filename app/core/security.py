import bcrypt
from datetime import datetime, timedelta
from typing import Any
from jose import jwt
from app.core.config import settings
from starlette.requests import Request


ALGORITHM = "HS256"

# Function to create access token
def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:
    expire = datetime.utcnow() + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Function to verify password using bcrypt
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# Function to hash a password using bcrypt
def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')  # Convert bytes to string


def get_ip_address(request: Request) -> str:
    """
    Returns the ip address for the current request (or 127.0.0.1 if none found)
    based on the X-Forwarded-For and CF-Connecting-IP headers.
    """

    # First, check for the X-Forwarded-For header
    if "x-forwarded-for" in request.headers:
        return request.headers["x-forwarded-for"]

    # If not found, check for Cloudflare's CF-Connecting-IP header
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip

    # Fallback if no headers found
    if not request.client or not request.client.host:
        return "127.0.0.1"

    return request.client.host