from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from models import User, get_db, get_password_hash

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_current_user(request: Request, db: Session) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


@router.get("/signup", response_class=HTMLResponse)
def signup_get(request: Request):
    return templates.TemplateResponse(
        "signup.html",
        {"request": request, "error": None},
    )


@router.post("/signup", response_class=HTMLResponse)
def signup_post(
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    existing_email = db.query(User).filter(User.email == email).first()
    existing_username = db.query(User).filter(User.username == username).first()
    if existing_email or existing_username:
        return templates.TemplateResponse(
            "signup.html",
            {
                "request": request,
                "error": "Email ou nom d'utilisateur déjà utilisé.",
            },
        )

    user = User(
        email=email,
        username=username,
        password_hash=get_password_hash(password),
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    request.session["user_id"] = user.id
    return RedirectResponse(url="/profile", status_code=303)


@router.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None},
    )


@router.post("/login", response_class=HTMLResponse)
def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.verify_password(password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Identifiants invalides."},
        )

    request.session["user_id"] = user.id
    return RedirectResponse(url="/profile", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)
