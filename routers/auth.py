from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import SignupRequest, UserResponse, LoginRequest, LoginResponse, Token
from auth import get_password_hash, verify_password, create_access_token, get_current_active_user
from datetime import timedelta
from config import settings

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_data: SignupRequest, db: Session = Depends(get_db)):
    """Create a new user account with work email validation"""
    # Email validation is handled by Pydantic validator, but double-check here
    email_lower = user_data.email.lower()
    domain = email_lower.split('@')[-1] if '@' in email_lower else ''
    
    personal_domains = ['gmail.com', 'hotmail.com', 'yahoo.com', 'yahoo.co.uk', 'yahoo.co.in',
                        'outlook.com', 'live.com', 'msn.com', 'aol.com', 'icloud.com',
                        'mail.com', 'protonmail.com', 'zoho.com', 'yandex.com', 'gmx.com']
    
    if domain in personal_domains:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Personal email accounts are not allowed. Please use your work email address. "
                   f"Rejected domains include: {', '.join(personal_domains[:5])} and others."
        )
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == email_lower).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )
    
    # Validate referral fields
    if user_data.was_referred == "yes":
        if not user_data.referrer_name and not user_data.referrer_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please provide either referrer name or email when you were referred by someone"
            )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=email_lower,
        password=hashed_password,
        name=user_data.name,
        company=user_data.company,
        department=user_data.department,
        role=user_data.role,
        was_referred=user_data.was_referred,
        referrer_name=user_data.referrer_name if user_data.was_referred == "yes" else None,
        referrer_email=user_data.referrer_email.lower() if user_data.was_referred == "yes" and user_data.referrer_email else None
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=LoginResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return access token"""
    # Find user
    user = db.query(User).filter(User.email == login_data.email.lower()).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(login_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email},
        expires_delta=access_token_expires
    )
    
    return LoginResponse(
        message="Login successful",
        user=user,
        token=Token(access_token=access_token, token_type="bearer")
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current authenticated user information"""
    return current_user

