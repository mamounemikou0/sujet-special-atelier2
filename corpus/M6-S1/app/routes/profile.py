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


@router.get("/profile", response_class=HTMLResponse)
def profile_get(
    request: Request,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "user": user, "error": None, "success": None},
    )


@router.post("/profile", response_class=HTMLResponse)
def profile_post(
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    current_password: str = Form(...),
    new_password: str | None = Form(None),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not user.verify_password(current_password):
        return templates.TemplateResponse(
            "profile.html",
            {
                "request": request,
                "user": user,
                "error": "Mot de passe actuel incorrect.",
                "success": None,
            },
        )

    # Check email/username uniqueness (excluding self)
    existing_email = (
        db.query(User)
        .filter(User.email == email, User.id != user.id)
        .first()
    )
    existing_username = (
        db.query(User)
        .filter(User.username == username, User.id != user.id)
        .first()
    )
    if existing_email or existing_username:
        return templates.TemplateResponse(
            "profile.html",
            {
                "request": request,
                "user": user,
                "error": "Email ou nom d'utilisateur déjà utilisé.",
                "success": None,
            },
        )

    user.email = email
    user.username = username
    if new_password:
        user.password_hash = get_password_hash(new_password)

    db.add(user)
    db.commit()
    db.refresh(user)

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": user,
            "error": None,
            "success": "Profil mis à jour avec succès.",
        },
    )


@router.post("/profile/delete")
def delete_own_account(
    request: Request,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    db.delete(user)
    db.commit()
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)
