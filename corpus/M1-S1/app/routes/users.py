from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from models import SessionLocal, User
from passlib.context import CryptContext

router = APIRouter()

templates = Jinja2Templates(directory="templates")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_current_user(request: Request):
    user_id = request.cookies.get("user_id")

    if not user_id:
        return None

    db = SessionLocal()

    user = db.query(User).filter(User.id == int(user_id)).first()

    db.close()

    return user


@router.get("/profile")
def profile(request: Request):
    user = get_current_user(request)

    if not user:
        return RedirectResponse("/login", status_code=303)

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": user
        }
    )


@router.post("/profile/update")
def update_profile(
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...)
):
    current_user = get_current_user(request)

    if not current_user:
        return RedirectResponse("/login", status_code=303)

    db = SessionLocal()

    user = db.query(User).filter(User.id == current_user.id).first()

    user.email = email
    user.username = username

    if password.strip():
        user.password = pwd_context.hash(password)

    db.commit()

    db.close()

    return RedirectResponse("/profile", status_code=303)


@router.get("/users")
def users_list(request: Request):
    current_user = get_current_user(request)

    if not current_user:
        return RedirectResponse("/login", status_code=303)

    db = SessionLocal()

    users = db.query(User).all()

    db.close()

    return templates.TemplateResponse(
        "users.html",
        {
            "request": request,
            "users": users,
            "current_user": current_user
        }
    )


@router.get("/delete-account")
def delete_account(request: Request):
    current_user = get_current_user(request)

    if not current_user:
        return RedirectResponse("/login", status_code=303)

    db = SessionLocal()

    user = db.query(User).filter(User.id == current_user.id).first()

    db.delete(user)
    db.commit()

    db.close()

    response = RedirectResponse("/register", status_code=303)
    response.delete_cookie("user_id")

    return response