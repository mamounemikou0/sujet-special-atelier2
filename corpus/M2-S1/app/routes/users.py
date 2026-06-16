from fastapi import APIRouter, Depends, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from models import User, get_db
from passlib.context import CryptContext

router = APIRouter()
templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    users = db.query(User).all()
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "current_user": current_user, "users": users}
    )


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(
        "profile.html", {"request": request, "current_user": current_user, "success": None, "error": None}
    )


@router.post("/profile")
async def update_profile(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    current_password: str = Form(""),
    new_password: str = Form(""),
    db: Session = Depends(get_db),
):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    # Check username uniqueness
    existing = db.query(User).filter(User.username == username, User.id != current_user.id).first()
    if existing:
        return templates.TemplateResponse(
            "profile.html",
            {"request": request, "current_user": current_user, "error": "Ce nom d'utilisateur est déjà pris.", "success": None},
            status_code=400,
        )

    # Check email uniqueness
    existing_email = db.query(User).filter(User.email == email, User.id != current_user.id).first()
    if existing_email:
        return templates.TemplateResponse(
            "profile.html",
            {"request": request, "current_user": current_user, "error": "Cet email est déjà utilisé.", "success": None},
            status_code=400,
        )

    current_user.username = username
    current_user.email = email

    if new_password:
        if not current_password:
            return templates.TemplateResponse(
                "profile.html",
                {"request": request, "current_user": current_user, "error": "Mot de passe actuel requis pour changer de mot de passe.", "success": None},
                status_code=400,
            )
        if not pwd_context.verify(current_password, current_user.hashed_password):
            return templates.TemplateResponse(
                "profile.html",
                {"request": request, "current_user": current_user, "error": "Mot de passe actuel incorrect.", "success": None},
                status_code=400,
            )
        if len(new_password) < 6:
            return templates.TemplateResponse(
                "profile.html",
                {"request": request, "current_user": current_user, "error": "Le nouveau mot de passe doit faire au moins 6 caractères.", "success": None},
                status_code=400,
            )
        current_user.hashed_password = pwd_context.hash(new_password)

    db.commit()
    db.refresh(current_user)
    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "current_user": current_user, "success": "Profil mis à jour avec succès.", "error": None},
    )


@router.get("/profile/{user_id}", response_class=HTMLResponse)
async def view_profile(request: Request, user_id: int, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    if not current_user.is_admin and current_user.id != user_id:
        return RedirectResponse(url="/dashboard", status_code=302)
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(
        "view_profile.html", {"request": request, "current_user": current_user, "target_user": target_user}
    )


@router.post("/delete/{user_id}")
async def delete_user(request: Request, user_id: int, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    # Only admin or the user themselves can delete
    if not current_user.is_admin and current_user.id != user_id:
        return RedirectResponse(url="/dashboard", status_code=302)

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        return RedirectResponse(url="/dashboard", status_code=302)

    # Prevent admin from deleting themselves
    if target_user.is_admin and current_user.id == target_user.id:
        return RedirectResponse(url="/dashboard?error=admin_delete", status_code=302)

    db.delete(target_user)
    db.commit()

    if current_user.id == user_id:
        request.session.clear()
        return RedirectResponse(url="/login", status_code=302)

    return RedirectResponse(url="/dashboard", status_code=302)
