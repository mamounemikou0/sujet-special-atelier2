from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from models import SessionLocal, User
from passlib.context import CryptContext

router = APIRouter()

templates = Jinja2Templates(directory="templates")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get("/")
def home():
    return RedirectResponse("/login")


@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(
        "register.html",
        {"request": request}
    )


@router.post("/register")
def register(
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...)
):
    db = SessionLocal()

    existing_user = db.query(User).filter(
        (User.email == email) | (User.username == username)
    ).first()

    if existing_user:
        db.close()
        return RedirectResponse("/register", status_code=303)

    new_user = User(
        email=email,
        username=username,
        password=pwd_context.hash(password)
    )

    db.add(new_user)
    db.commit()

    db.close()

    return RedirectResponse("/login", status_code=303)


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    db = SessionLocal()

    user = db.query(User).filter(
        User.username == username
    ).first()

    if not user:
        db.close()
        return RedirectResponse("/login", status_code=303)

    if not pwd_context.verify(password, user.password):
        db.close()
        return RedirectResponse("/login", status_code=303)

    response = RedirectResponse("/profile", status_code=303)

    response.set_cookie(
        key="user_id",
        value=str(user.id)
    )

    db.close()

    return response


@router.get("/logout")
def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie("user_id")
    return response