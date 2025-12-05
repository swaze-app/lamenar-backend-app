from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from config import settings
from core import get_db
from models import User
from schemas import TokenData
import hashlib

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# Bcrypt has a 72-byte limit, so we pre-hash longer passwords with SHA-256
BCRYPT_MAX_LENGTH = 72


def _preprocess_password(password: str) -> str:
    """
    Preprocess password for bcrypt.
    If password is longer than 72 bytes when UTF-8 encoded, hash it with SHA-256 first.
    This preserves all entropy while staying within bcrypt's limit.
    Returns a string that, when UTF-8 encoded, is guaranteed to be <= 72 bytes.
    """
    password_bytes = password.encode('utf-8')
    
    # If already <= 72 bytes, return as-is
    if len(password_bytes) <= BCRYPT_MAX_LENGTH:
        return password
    
    # For passwords > 72 bytes, hash with SHA-256 to get 32 bytes
    # Then use hex encoding to get a 64-character string (64 bytes when UTF-8 encoded)
    sha256_digest = hashlib.sha256(password_bytes).digest()
    hex_hash = sha256_digest.hex()
    
    # Double-check the encoded length
    encoded_length = len(hex_hash.encode('utf-8'))
    if encoded_length > BCRYPT_MAX_LENGTH:
        # Fallback: use base64 which is shorter (44 chars = 44 bytes)
        import base64
        base64_hash = base64.b64encode(sha256_digest).decode('utf-8')
        if len(base64_hash.encode('utf-8')) <= BCRYPT_MAX_LENGTH:
            return base64_hash
        # Last resort: truncate hex
        return hex_hash[:BCRYPT_MAX_LENGTH]
    
    return hex_hash


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    password_for_bcrypt = _preprocess_password(plain_password)
    # Final safety check before passing to passlib
    encoded_bytes = password_for_bcrypt.encode('utf-8')
    if len(encoded_bytes) > BCRYPT_MAX_LENGTH:
        # This should never happen, but truncate if it does
        password_for_bcrypt = password_for_bcrypt[:BCRYPT_MAX_LENGTH]
    return pwd_context.verify(password_for_bcrypt, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password, handling passwords longer than bcrypt's 72-byte limit"""
    # Preprocess the password
    password_for_bcrypt = _preprocess_password(password)
    
    # Convert to bytes to check exact length
    password_bytes = password_for_bcrypt.encode('utf-8')
    
    # If somehow still > 72 bytes, truncate the bytes directly
    if len(password_bytes) > BCRYPT_MAX_LENGTH:
        password_bytes = password_bytes[:BCRYPT_MAX_LENGTH]
        password_for_bcrypt = password_bytes.decode('utf-8', errors='ignore')
    
    # Ensure we have a valid string
    if not password_for_bcrypt:
        raise ValueError("Password preprocessing resulted in empty string")
    
    try:
        return pwd_context.hash(password_for_bcrypt)
    except ValueError as e:
        # If we still get the error, try with direct byte truncation
        if "72 bytes" in str(e):
            # Last resort: truncate original password to 72 bytes
            original_bytes = password.encode('utf-8')[:BCRYPT_MAX_LENGTH]
            truncated_password = original_bytes.decode('utf-8', errors='ignore')
            return pwd_context.hash(truncated_password)
        raise


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str, credentials_exception: HTTPException) -> TokenData:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        if user_id is None or email is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id, email=email)
        return token_data
    except JWTError:
        raise credentials_exception


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = verify_token(token, credentials_exception)
    user = db.query(User).filter(User.id == token_data.user_id).first()
    
    if user is None:
        raise credentials_exception
    
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current active user (can be extended for user status checks)"""
    return current_user

