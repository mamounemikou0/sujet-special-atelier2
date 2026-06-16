from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from models import User, get_db, pwd_context
from routes.auth import get_current_user
from jose import jwt

router = APIRouter(prefix="/users", tags=["users"])
templates = Jinja2Templates(directory="templates")

# Route pour le profil utilisateur
@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("profile.html", {"request": request, "user": current_user})

@router.post("/profile")
async def update_profile(
    request: Request,
    response: Response,
    username: str,
    email: str,
    new_password: Optional[str] = None,
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)

    # Mettre à jour les informations
    current_user.username = username
    current_user.email = email
    if new_password:
        current_user.hashed_password = pwd_context.hash(new_password)
    db.commit()
    db.refresh(current_user)

    # Mettre à jour le token JWT si le nom d'utilisateur a changé
    if current_user.username != username:
        access_token = jwt.encode(
            {"sub": current_user.username, "exp": datetime.utcnow() + timedelta(minutes=30)},
            "ta_clé_secrète_à_changer_en_production",
            algorithm="HS256"
        )
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=30 * 60,
            expires=30 * 60
        )

    return RedirectResponse(url="/users/profile", status_code=status.HTTP_303_SEE_OTHER)

# Route pour la liste des utilisateurs
@router.get("/list", response_class=HTMLResponse)
async def users_list(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    users = db.query(User).all()
    return templates.TemplateResponse("users.html", {"request": request, "users": users, "current_user": current_user})

# Route pour supprimer son propre compte
@router.post("/delete")
async def delete_account(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    db.delete(current_user)
    db.commit()
    return RedirectResponse(url="/auth/logout", status_code=status.HTTP_303_SEE_OTHER)