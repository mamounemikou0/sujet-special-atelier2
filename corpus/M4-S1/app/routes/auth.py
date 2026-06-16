from fastapi import APIRouter, Request, Depends, HTTPException, status, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from models import User, get_db, pwd_context
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="templates")
SECRET_KEY = "ta_clé_secrète_à_changer_en_production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Route pour l'inscription
@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
async def register(
    request: Request,
    username: str,
    email: str,
    password: str,
    db: Session = Depends(get_db)
):
    # Vérifier si l'utilisateur ou l'email existe déjà
    db_user = db.query(User).filter(User.username == username).first()
    db_email = db.query(User).filter(User.email == email).first()
    if db_user or db_email:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Nom d'utilisateur ou email déjà utilisé."}
        )

    # Créer un nouvel utilisateur
    hashed_password = pwd_context.hash(password)
    new_user = User(username=username, email=email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Rediriger vers la page de connexion
    return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)

# Route pour la connexion
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(
    request: Request,
    response: Response,
    username: str,
    password: str,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Nom d'utilisateur ou mot de passe incorrect."}
        )

    # Créer un token JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt.encode(
        {"sub": user.username, "exp": datetime.utcnow() + access_token_expires},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    # Définir le cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

# Route pour la déconnexion
@router.get("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)