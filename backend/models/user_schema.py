from pydantic import BaseModel, EmailStr
from typing import Optional

# Base User Schema
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(UserBase):
    password: str

class UserProfileUpdate(BaseModel):
    skills: Optional[str] = None
    job_level: Optional[str] = None
    company: Optional[str] = None
    primary_language: Optional[str] = None
    coding_style: Optional[str] = None
    schooling: Optional[str] = None
    linkedin_url: Optional[str] = None

class UserResponse(UserBase):
    id: int
    skills: Optional[str] = None
    job_level: Optional[str] = None
    company: Optional[str] = None
    primary_language: Optional[str] = None
    coding_style: Optional[str] = None
    schooling: Optional[str] = None
    linkedin_url: Optional[str] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
