from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
from jose import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose.exceptions import JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
from database import get_db
import models

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def authenticate_user(db: Session, email: str, password: str):
    user = get_user(db, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(username=email)
    except JWTError:
        raise credentials_exception
    if token_data.username is None:
        raise credentials_exception
    user = get_user(db, email=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: Annotated[models.User, Depends(get_current_user)]):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_role(required_roles: list[str]):
    def role_checker(current_user: Annotated[models.User, Depends(get_current_active_user)]):
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker

def require_admin(current_user: Annotated[models.User, Depends(get_current_active_user)]):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user

def require_supervisor_or_admin(current_user: Annotated[models.User, Depends(get_current_active_user)]):
    if current_user.role not in ["supervisor", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Supervisor or admin access required")
    return current_user

def require_manager_or_above(current_user: Annotated[models.User, Depends(get_current_active_user)]):
    if current_user.role not in ["manager", "supervisor", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager access or above required")
    return current_user


def require_contractor(current_user: Annotated[models.User, Depends(get_current_active_user)]):
    """Require contractor role for creating operational data records."""
    if current_user.role != "contractor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Contractor role required to create operational records"
        )
    return current_user


def require_engineer_or_above(current_user: Annotated[models.User, Depends(get_current_active_user)]):
    """Require engineer, manager, supervisor, or admin role for read access."""
    if current_user.role not in ["engineer", "manager", "supervisor", "admin", "contractor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Engineer access or above required"
        )
    return current_user
