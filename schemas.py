from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional, Literal
from datetime import datetime


# Personal email domains to reject
PERSONAL_EMAIL_DOMAINS = [
    'gmail.com', 'hotmail.com', 'yahoo.com', 'yahoo.co.uk', 'yahoo.co.in',
    'outlook.com', 'live.com', 'msn.com', 'aol.com', 'icloud.com',
    'mail.com', 'protonmail.com', 'zoho.com', 'yandex.com', 'gmx.com'
]


def validate_work_email(email: str) -> str:
    """Validate that email is not from a personal email provider"""
    email_lower = email.lower()
    domain = email_lower.split('@')[-1] if '@' in email_lower else ''
    
    if domain in PERSONAL_EMAIL_DOMAINS:
        raise ValueError(
            f"Personal email accounts are not allowed. Please use your work email. "
            f"Rejected domains include: {', '.join(PERSONAL_EMAIL_DOMAINS[:5])}..."
        )
    
    return email_lower


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1)
    company: str = Field(..., min_length=1, description="Company name is required")
    department: Optional[str] = None
    role: str = Field(..., min_length=1, description="Role is required")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    was_referred: Literal["yes", "no"] = Field(..., description="Were you referred by someone?")
    referrer_name: Optional[str] = None
    referrer_email: Optional[EmailStr] = None
    
    @field_validator('email')
    @classmethod
    def validate_email_domain(cls, v: str) -> str:
        """Validate email is not from personal email providers"""
        return validate_work_email(v)
    
    @model_validator(mode='after')
    def validate_referral_fields(self):
        """Validate referral fields are provided if was_referred is 'yes'"""
        if self.was_referred == "yes":
            if not self.referrer_name and not self.referrer_email:
                raise ValueError(
                    "Please provide either referrer name or email when you were referred by someone"
                )
        return self


class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(UserCreate):
    """Signup request with all required fields and email validation"""
    pass


class LoginResponse(BaseModel):
    message: str
    user: UserResponse
    token: Token

