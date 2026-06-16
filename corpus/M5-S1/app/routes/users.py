from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from models import get_db, User
from routes.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "user": user}
    )

@router.post("/profile/update")
async def update_profile(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    current_password: str = Form(None),
    new_password: str = Form(None),
    db: Session = Depends(get_db)
):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
    # Vérifier si le nouveau nom d'utilisateur ou email est déjà pris
    existing_user = db.query(User).filter(
        ((User.username == username) | (User.email == email)) & (User.id != user.id)
    ).first()
    
    if existing_user:
        return templates.TemplateResponse(
            "profile.html",
            {
                "request": request,
                "user": user,
                "error": "Nom d'utilisateur ou email déjà utilisé"
            }
        )
    
    # Mettre à jour les informations
    user.username = username
    user.email = email
    
    # Changer le mot de passe si demandé
    if current_password and new_password:
        if not user.verify_password(current_password):
            return templates.TemplateResponse(
                "profile.html",
                {
                    "request": request,
                    "user": user,
                    "error": "Mot de passe actuel incorrect"
                }
            )
        user.hashed_password = User.hash_password(new_password)
    
    db.commit()
    
    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": user,
            "success": "Profil mis à jour avec succès"
        }
    )

@router.get("/users", response_class=HTMLResponse)
async def list_users(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
    users = db.query(User).all()
    return templates.TemplateResponse(
        "users.html",
        {"request": request, "user": user, "users": users}
    )

@router.post("/users/delete/{user_id}")
async def delete_user(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db)
):
    current_user = await get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login")
    
    user_to_delete = db.query(User).filter(User.id == user_id).first()
    if not user_to_delete:
        return {"error": "Utilisateur non trouvé"}
    
    # Vérifier les permissions
    if current_user.id != user_id and not current_user.is_admin:
        return {"error": "Permission refusée"}
    
    # Empêcher la suppression de l'admin par un non-admin
    if user_to_delete.is_admin and not current_user.is_admin:
        return {"error": "Impossible de supprimer un administrateur"}
    
    # Si l'utilisateur supprime son propre compte, le déconnecter
    if current_user.id == user_id:
        db.delete(user_to_delete)
        db.commit()
        response = RedirectResponse(url="/login")
        response.delete_cookie("access_token")
        return response
    
    db.delete(user_to_delete)
    db.commit()
    
    return RedirectResponse(url="/users", status_code=303)