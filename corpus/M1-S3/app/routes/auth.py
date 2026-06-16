from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeSerializer, BadSignature
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from models import get_db, User

router = APIRouter()
templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
serializer = URLSafeSerializer("change-this-secret-key-in-production")
COOKIE_NAME = "shop_session"

def get_current_user(request: Request, db: Session):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        user_id = serializer.loads(token)
    except BadSignature:
        return None
    return db.query(User).filter(User.id == int(user_id)).first()

def require_user(request: Request, db: Session):
    user = get_current_user(request, db)
    if not user:
        return None
    return user

def require_admin(request: Request, db: Session):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return None
    return user

def set_login_cookie(response: Response, user: User):
    response.set_cookie(COOKIE_NAME, serializer.dumps(user.id), httponly=True, samesite="lax")

@router.get("/register")
def register_page(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("register.html", {"request": request, "user": get_current_user(request, db), "error": None})

@router.post("/register")
def register(request: Request, email: str = Form(...), password: str = Form(...), full_name: str = Form(...), shipping_address: str = Form(""), db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == email.lower()).first():
        return templates.TemplateResponse("register.html", {"request": request, "user": None, "error": "Cet email est déjà utilisé."})
    user = User(email=email.lower(), password_hash=pwd_context.hash(password), full_name=full_name, shipping_address=shipping_address, role="customer")
    db.add(user); db.commit(); db.refresh(user)
    response = RedirectResponse("/", status_code=303)
    set_login_cookie(response, user)
    return response

@router.get("/login")
def login_page(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("login.html", {"request": request, "user": get_current_user(request, db), "error": None})

@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user or not pwd_context.verify(password, user.password_hash):
        return templates.TemplateResponse("login.html", {"request": request, "user": None, "error": "Identifiants invalides."})
    response = RedirectResponse("/", status_code=303)
    set_login_cookie(response, user)
    return response

@router.get("/logout")
def logout():
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie(COOKIE_NAME)
    return response

@router.get("/account")
def account(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse("account.html", {"request": request, "user": user, "message": None})

@router.post("/account")
def update_account(request: Request, full_name: str = Form(...), shipping_address: str = Form(""), db: Session = Depends(get_db)):
    user = require_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    user.full_name = full_name
    user.shipping_address = shipping_address
    db.commit()
    return templates.TemplateResponse("account.html", {"request": request, "user": user, "message": "Compte mis à jour."})
