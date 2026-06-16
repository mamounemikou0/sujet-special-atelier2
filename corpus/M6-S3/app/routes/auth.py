from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from models import User, get_db, hash_password
from session_store import create_session, destroy_session
from deps import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/login")
def login_page(request: Request, user=Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "user": user})


@router.post("/login")
def login(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()
    if not user or user.password_hash != hash_password(password):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Identifiants invalides",
                "user": None,
            },
            status_code=400,
        )
    session_id = create_session(user.id)
    resp = RedirectResponse(url="/", status_code=302)
    resp.set_cookie("session_id", session_id, httponly=True)
    return resp


@router.get("/register")
def register_page(request: Request, user=Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(
        "register.html", {"request": request, "user": user}
    )


@router.post("/register")
def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    address: str = Form(""),
    db: Session = Depends(get_db),
):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "Un compte existe déjà avec cet email",
                "user": None,
            },
            status_code=400,
        )
    user = User(
        email=email,
        password_hash=hash_password(password),
        is_admin=False,
        address=address,
    )
    db.add(user)
    db.commit()
    return RedirectResponse(url="/login", status_code=302)


@router.get("/logout")
def logout(response: Response, session_id: str | None = None):
    if session_id:
        destroy_session(session_id)
    resp = RedirectResponse(url="/", status_code=302)
    resp.delete_cookie("session_id")
    return resp
