from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from models import get_db, User
from jose import jwt
from datetime import datetime, timedelta

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Configuration JWT
SECRET_KEY = "votre-cle-secrete-tres-longue-et-complexe-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        user = db.query(User).filter(User.username == username).first()
        return user
    except:
        return None

@router.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Vérifier si l'utilisateur existe déjà
    existing_user = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()
    
    if existing_user:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Nom d'utilisateur ou email déjà utilisé"}
        )
    
    # Créer le nouvel utilisateur
    new_user = User(
        username=username,
        email=email,
        hashed_password=User.hash_password(password)
    )
    db.add(new_user)
    db.commit()
    
    return RedirectResponse(url="/login", status_code=303)

@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    
    if not user or not user.verify_password(password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Nom d'utilisateur ou mot de passe incorrect"}
        )
    
    # Créer le token JWT
    access_token = create_access_token(data={"sub": user.username})
    
    response = RedirectResponse(url="/profile", status_code=303)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    return response

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response