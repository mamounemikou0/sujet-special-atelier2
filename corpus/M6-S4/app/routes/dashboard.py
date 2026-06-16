from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from models import SessionLocal, User
from .auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)

    if user.role == "employee":
        return templates.TemplateResponse(
            "dashboard_employee.html",
            {"request": request, "user": user},
        )
    elif user.role == "manager":
        return templates.TemplateResponse(
            "dashboard_manager.html",
            {"request": request, "user": user},
        )
    elif user.role == "admin":
        return templates.TemplateResponse(
            "dashboard_admin.html",
            {"request": request, "user": user},
        )
    else:
        return RedirectResponse("/login", status_code=303)
