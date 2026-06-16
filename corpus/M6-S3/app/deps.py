from typing import Optional

from fastapi import Depends, Cookie, HTTPException, status
from sqlalchemy.orm import Session

from models import User, get_db
from session_store import SESSIONS


def get_current_user(
    db: Session = Depends(get_db),
    session_id: Optional[str] = Cookie(default=None),
) -> Optional[User]:
    if not session_id:
        return None
    user_id = SESSIONS.get(session_id)
    if not user_id:
        return None
    user = db.query(User).filter(User.id == user_id).first()
    return user


def require_user(user: User = Depends(get_current_user)) -> User:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification requise",
        )
    return user


def require_admin(user: User = Depends(require_user)) -> User:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès administrateur requis",
        )
    return user
