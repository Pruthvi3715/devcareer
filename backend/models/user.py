from sqlalchemy import Column, Integer, String, Text
from models.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Profile fields
    skills = Column(Text, nullable=True) # Could be JSON, storing as text for simplicity
    job_level = Column(String, nullable=True)
    company = Column(String, nullable=True)
    primary_language = Column(String, nullable=True)
    coding_style = Column(String, nullable=True)
    schooling = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
