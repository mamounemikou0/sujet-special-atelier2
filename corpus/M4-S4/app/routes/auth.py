from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from models import User, Role
from main import get_db, pwd_context, templates
from typing import Optional

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login_post(request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()
    email = form_data.get("email")
    password = form_data.get("password")

    user = db.query(User).filter(User.email == email).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Email ou mot de passe incorrect"})

    request.session["user_id"] = user.id
    request.session["role"] = user.role.value

    if user.role == Role.ADMIN:
        return RedirectResponse(url="/admin/dashboard", status_code=303)
    elif user.role == Role.MANAGER:
        return RedirectResponse(url="/manager/dashboard", status_code=303)
    else:
        return RedirectResponse(url="/employee/dashboard", status_code=303)

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)