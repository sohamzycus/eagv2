"""
🐦 BirdSense API - Authentication Routes
Developed by Soham
"""

from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends

from api.models import UserLogin, Token, UserInfo
from api.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token, summary="Login and get JWT token")
async def login(credentials: UserLogin):
    """
    Authenticate user and return JWT token.
    
    **Default Users:**
    - `mazycus` / `ZycusMerlinAssist@2024` (Admin)
    - `demo` / `demo123` (Demo user)
    - `soham` / `birdsense2024` (Developer)
    """
    user = authenticate_user(credentials.username, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserInfo, summary="Get current user info")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get information about the currently authenticated user."""
    return UserInfo(
        username=current_user["username"],
        email=current_user.get("email"),
        full_name=current_user.get("full_name"),
        is_active=current_user.get("is_active", True)
    )


@router.post("/refresh", response_model=Token, summary="Refresh JWT token")
async def refresh_token(current_user: dict = Depends(get_current_user)):
    """Get a new JWT token (extends session)."""
    access_token = create_access_token(
        data={"sub": current_user["username"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

