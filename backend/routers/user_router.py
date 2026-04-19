from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from models.user import User
from models.user_schema import UserResponse, UserProfileUpdate
from models.db import get_db
from services.auth import SECRET_KEY, ALGORITHM

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

@router.get("/profile", response_model=UserResponse)
def get_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/profile", response_model=UserResponse)
def update_user_profile(
    profile_update: UserProfileUpdate, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # Update fields if provided
    update_data = profile_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(current_user, key, value)
        
    db.commit()
    db.refresh(current_user)
    return current_user
