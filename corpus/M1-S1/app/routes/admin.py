from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from models import SessionLocal, User

router = APIRouter()

templates = Jinja2Templates(directory="templates")


def get_current_user(request: Request):
    user_id = request.cookies.get("user_id")

    if not user_id:
        return None

    db = SessionLocal()

    user = db.query(User).filter(User.id == int(user_id)).first()

    db.close()

    return user


@router.get("/admin/users")
def admin_users(request: Request):
    current_user = get_current_user(request)

    if not current_user or not current_user.is_admin:
        return RedirectResponse("/login", status_code=303)

    db = SessionLocal()

    users = db.query(User).all()

    db.close()

    return templates.TemplateResponse(
        "admin_users.html",
        {
            "request": request,
            "users": users
        }
    )


@router.get("/admin/delete/{user_id}")
def admin_delete_user(user_id: int, request: Request):
    current_user = get_current_user(request)

    if not current_user or not current_user.is_admin:
        return RedirectResponse("/login", status_code=303)

    db = SessionLocal()

    user = db.query(User).filter(User.id == user_id).first()

    if user:
        db.delete(user)
        db.commit()

    db.close()

    return RedirectResponse("/admin/users", status_code=303)