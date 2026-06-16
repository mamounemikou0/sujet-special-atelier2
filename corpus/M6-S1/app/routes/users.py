from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from models import User, get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_current_user(request: Request, db: Session) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


@router.get("/users", response_class=HTMLResponse)
def list_users(
    request: Request,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    users = db.query(User).order_by(User.created_at.desc()).all()
    return templates.TemplateResponse(
        "users.html",
        {
            "request": request,
            "user": user,
            "users": users,
        },
    )


@router.post("/admin/users/{user_id}/delete")
def admin_delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    current_user = get_current_user(request, db)
    if not current_user or not current_user.is_admin:
        return RedirectResponse(url="/login", status_code=303)

    user_to_delete = db.query(User).filter(User.id == user_id).first()
    if user_to_delete:
        # Prevent admin from deleting themselves accidentally (optional)
        if user_to_delete.id != current_user.id:
            db.delete(user_to_delete)
            db.commit()

    return RedirectResponse(url="/users", status_code=303)
