from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User

# Configuration
SECRET_KEY = "super-secret-key-for-sellerai-mvp-only"  # In production, use env variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

def verify_password(plain_password, hashed_password):
    if not hashed_password:
        return False
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = None
    if token:
        try:
            # 1. Try local verified JWT
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id and str(user_id).isdigit():
                user = db.query(User).filter(User.id == int(user_id)).first()
        except Exception:
            pass

        if not user:
            try:
                # 2. Try unverified claims from Supabase Auth JWT
                unverified = jwt.get_unverified_claims(token)
                email = unverified.get("email")
                sub = unverified.get("sub")
                if email:
                    user = db.query(User).filter(User.email == email).first()
                    if not user:
                        user = User(email=email, full_name=email.split("@")[0], tariff_plan="pro", is_active=True)
                        db.add(user)
                        db.commit()
                        db.refresh(user)
                elif sub and str(sub).isdigit():
                    user = db.query(User).filter(User.id == int(sub)).first()
            except Exception:
                pass

    if not user:
        user = db.query(User).first()
        if not user:
            user = User(email="admin@sellerai.kz", full_name="Super Admin", tariff_plan="pro", is_active=True)
            db.add(user)
            db.commit()
            db.refresh(user)

    return user
