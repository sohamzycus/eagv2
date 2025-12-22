"""
🐦 BirdSense API - JWT Authentication
Developed by Soham

JWT-based authentication for the REST API.
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# ============ CONFIG ============

# Secret key - in production, use environment variable
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "birdsense-secret-key-change-in-production-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token security
security = HTTPBearer()


# ============ DEFAULT USERS ============
# In production, use a proper database

USERS_DB = {
    "mazycus": {
        "username": "mazycus",
        "hashed_password": pwd_context.hash("ZycusMerlinAssist@2024"),
        "email": "mazycus@zycus.com",
        "full_name": "Mazycus Admin",
        "is_active": True
    },
    "demo": {
        "username": "demo",
        "hashed_password": pwd_context.hash("demo123"),
        "email": "demo@birdsense.app",
        "full_name": "Demo User",
        "is_active": True
    },
    "soham": {
        "username": "soham",
        "hashed_password": pwd_context.hash("birdsense2024"),
        "email": "soham@birdsense.app",
        "full_name": "Soham (Developer)",
        "is_active": True
    }
}


# ============ PASSWORD FUNCTIONS ============

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


# ============ USER FUNCTIONS ============

def get_user(username: str) -> Optional[dict]:
    """Get user from database."""
    return USERS_DB.get(username)


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate user with username and password."""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


# ============ JWT FUNCTIONS ============

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )


# ============ DEPENDENCIES ============

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """Dependency to get the current authenticated user."""
    token = credentials.credentials
    
    try:
        payload = decode_token(token)
        username: str = payload.get("sub")
        
        if username is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: no username",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user = get_user(username)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not user.get("is_active", False):
        raise HTTPException(
            status_code=401,
            detail="User is inactive"
        )
    
    return user


# Optional auth - allows unauthenticated access but provides user if token present
# Note: This function is not used in current API - keeping for future use
def get_current_user_optional():
    """Optional authentication - returns None if no token."""
    return None  # Placeholder - implement if needed

