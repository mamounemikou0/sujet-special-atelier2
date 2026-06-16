import hashlib
from fastapi import APIRouter, Request, Form, responses
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from models import SessionLocal, User
from jose import jwt

router = APIRouter()
templates = Jinja2Templates(directory="templates")

SECRET_KEY = "supersecretkeyfortoken"
ALGORITHM = "HS256"

@router.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    hashed = hashlib.sha256(password.encode()).hexdigest()
    user = db.query(User).filter(User.email == email, User.hashed_password == hashed).first()
    db.close()
    
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Identifiants incorrects"})
    
    token = jwt.encode({"user_id": user.id, "role": user.role}, SECRET_KEY, algorithm=ALGORITHM)
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response

@router.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response