from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from models import User, get_db
from routes.auth import get_current_user, get_password_hash

router = APIRouter(prefix="/api/users", tags=["users"])

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserResponse)
def update_user_me(user_update: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user_update.username:
        # Check if username is taken by someone else
        existing = db.query(User).filter(User.username == user_update.username, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username unavailable")
        current_user.username = user_update.username
        
    if user_update.email:
        existing = db.query(User).filter(User.email == user_update.email, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email unavailable")
        current_user.email = user_update.email
        
    if user_update.password:
        current_user.hashed_password = get_password_hash(user_update.password)

    db.commit()
    db.refresh(current_user)
    return current_user

@router.delete("/me")
def delete_user_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(current_user)
    db.commit()
    return {"message": "Account deleted successfully"}

@router.get("/", response_model=List[UserResponse])
def read_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@router.delete("/{user_id}")
def delete_user(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    user_to_delete = db.query(User).filter(User.id == user_id).first()
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")
        
    db.delete(user_to_delete)
    db.commit()
    return {"message": "User deleted by admin"}