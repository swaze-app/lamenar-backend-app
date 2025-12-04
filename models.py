from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.sql import func
from database import Base
import uuid


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)  # Hashed password
    name = Column(String, nullable=False)
    company = Column(String, nullable=False)  # Required field
    department = Column(String, nullable=True)
    role = Column(String, nullable=False)  # Required field
    was_referred = Column(String, nullable=False)  # "yes" or "no"
    referrer_name = Column(String, nullable=True)  # If was_referred is "yes"
    referrer_email = Column(String, nullable=True)  # If was_referred is "yes"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

