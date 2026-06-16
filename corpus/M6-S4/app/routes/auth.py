from hashlib import sha256
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from models import SessionLocal, User

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(p: str) -> str:
    return sha256(p.encode("utf-8")).hexdigest()


def get_current_user(request: Request, db: Session) -> Optional[User]:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


@router.get("/login")
def login_page(request: Request):
    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="templates")
    return templates.TemplateResponse(
        "login.html", {"request": request, "error": None}
    )


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()
    templates = __import__("fastapi").templating.Jinja2Templates(
        directory="templates"
    )
    if not user or user.password_hash != hash_password(password):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Identifiants invalides",
            },
            status_code=400,
        )
    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)
