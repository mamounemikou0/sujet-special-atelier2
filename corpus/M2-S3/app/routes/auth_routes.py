from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from database import get_db
import models
import auth

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterIn(BaseModel):
    email: str
    password: str
    full_name: str


class LoginIn(BaseModel):
    email: str
    password: str


class ProfileUpdate(BaseModel):
    full_name: str
    address: str = ""
    city: str = ""
    postal_code: str = ""
    country: str = "Canada"


@router.post("/register")
def register(data: RegisterIn, response: Response, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = models.User(
        email=data.email,
        hashed_password=auth.hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = auth.create_access_token({"sub": str(user.id)})
    response.set_cookie("access_token", token, httponly=True, max_age=60 * 60 * 24 * 7, samesite="lax")
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "is_admin": user.is_admin}


@router.post("/login")
def login(data: LoginIn, response: Response, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user or not auth.verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = auth.create_access_token({"sub": str(user.id)})
    response.set_cookie("access_token", token, httponly=True, max_age=60 * 60 * 24 * 7, samesite="lax")
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "is_admin": user.is_admin}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"ok": True}


@router.get("/me")
def me(current_user: models.User = Depends(auth.get_current_user)):
    if not current_user:
        return None
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "address": current_user.address,
        "city": current_user.city,
        "postal_code": current_user.postal_code,
        "country": current_user.country,
        "is_admin": current_user.is_admin,
    }


@router.put("/profile")
def update_profile(
    data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_user),
):
    current_user.full_name = data.full_name
    current_user.address = data.address
    current_user.city = data.city
    current_user.postal_code = data.postal_code
    current_user.country = data.country
    db.commit()
    return {"ok": True}
