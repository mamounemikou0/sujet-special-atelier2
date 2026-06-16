from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from models import User, get_db
from routes.auth import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")

# Route pour la page admin
@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user or not current_user.is_admin:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    users = db.query(User).all()
    return templates.TemplateResponse("admin.html", {"request": request, "users": users, "current_user": current_user})

# Route pour supprimer un utilisateur (admin uniquement)
@router.post("/delete_user/{user_id}")
async def delete_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user or not current_user.is_admin:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    user_to_delete = db.query(User).filter(User.id == user_id).first()
    if user_to_delete:
        db.delete(user_to_delete)
        db.commit()
    return RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)