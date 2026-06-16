from fastapi import APIRouter, Request, Depends, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session
from models import User, LeaveRequest, Role, Department
from main import get_db, templates, require_auth, UPLOAD_DIR, pwd_context
from datetime import date
import os
import pandas as pd
from io import StringIO
from werkzeug.utils import secure_filename

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    user = require_auth(request, db)
    if user.role != Role.ADMIN:
        return RedirectResponse(url="/", status_code=303)

    users = db.query(User).all()
    leave_requests = db.query(LeaveRequest).all()
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {"request": request, "user": user, "users": users, "leave_requests": leave_requests}
    )

@router.get("/users", response_class=HTMLResponse)
async def admin_users(request: Request, db: Session = Depends(get_db)):
    user = require_auth(request, db)
    if user.role != Role.ADMIN:
        return RedirectResponse(url="/", status_code=303)

    users = db.query(User).all()
    return templates.TemplateResponse("admin/users.html", {"request": request, "user": user, "users": users})

@router.get("/salaries", response_class=HTMLResponse)
async def admin_salaries(request: Request, db: Session = Depends(get_db)):
    user = require_auth(request, db)
    if user.role != Role.ADMIN:
        return RedirectResponse(url="/", status_code=303)

    users = db.query(User).all()
    return templates.TemplateResponse("admin/salaries.html", {"request": request, "user": user, "users": users})

@router.get("/export-users")
async def export_users(request: Request, db: Session = Depends(get_db)):
    user = require_auth(request, db)
    if user.role != Role.ADMIN:
        return RedirectResponse(url="/", status_code=303)

    users = db.query(User).all()
    data = [
        {
            "ID": user.id,
            "Nom": user.full_name,
            "Email": user.email,
            "Rôle": user.role.value,
            "Département": user.department.value,
            "Salaire": user.salary,
        }
        for user in users
    ]

    df = pd.DataFrame(data)
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, sep=";")
    csv_buffer.seek(0)

    return StreamingResponse(
        iter([csv_buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=employees.csv"}
    )

@router.get("/create-user", response_class=HTMLResponse)
async def create_user(request: Request, db: Session = Depends(get_db)):
    user = require_auth(request, db)
    if user.role != Role.ADMIN:
        return RedirectResponse(url="/", status_code=303)

    managers = db.query(User).filter(User.role == Role.MANAGER).all()
    return templates.TemplateResponse(
        "admin/create_user.html",
        {"request": request, "user": user, "managers": managers, "roles": [r.value for r in Role], "departments": [d.value for d in Department]}
    )

@router.post("/create-user")
async def create_user_post(request: Request, db: Session = Depends(get_db)):
    user = require_auth(request, db)
    if user.role != Role.ADMIN:
        return RedirectResponse(url="/", status_code=303)

    form_data = await request.form()
    email = form_data.get("email")
    full_name = form_data.get("full_name")
    password = form_data.get("password")
    role = form_data.get("role")
    department = form_data.get("department")
    salary = float(form_data.get("salary", 0))
    manager_id = form_data.get("manager_id")

    new_user = User(
        email=email,
        hashed_password=pwd_context.hash(password),
        full_name=full_name,
        role=Role(role),
        department=Department(department),
        salary=salary,
        manager_id=int(manager_id) if manager_id else None,
    )
    db.add(new_user)
    db.commit()

    return RedirectResponse(url="/admin/users", status_code=303)

@router.get("/edit-user/{user_id}", response_class=HTMLResponse)
async def edit_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_auth(request, db)
    if user.role != Role.ADMIN:
        return RedirectResponse(url="/", status_code=303)

    edited_user = db.query(User).filter(User.id == user_id).first()
    managers = db.query(User).filter(User.role == Role.MANAGER).all()
    return templates.TemplateResponse(
        "admin/edit_user.html",
        {
            "request": request,
            "user": user,
            "edited_user": edited_user,
            "managers": managers,
            "roles": [r.value for r in Role],
            "departments": [d.value for d in Department],
        }
    )

@router.post("/edit-user/{user_id}")
async def edit_user_post(user_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_auth(request, db)
    if user.role != Role.ADMIN:
        return RedirectResponse(url="/", status_code=303)

    form_data = await request.form()
    edited_user = db.query(User).filter(User.id == user_id).first()

    if edited_user:
        edited_user.email = form_data.get("email")
        edited_user.full_name = form_data.get("full_name")
        edited_user.role = Role(form_data.get("role"))
        edited_user.department = Department(form_data.get("department"))
        edited_user.salary = float(form_data.get("salary", 0))
        edited_user.manager_id = int(form_data.get("manager_id")) if form_data.get("manager_id") else None
        db.commit()

    return RedirectResponse(url="/admin/users", status_code=303)

@router.post("/delete-user/{user_id}")
async def delete_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_auth(request, db)
    if user.role != Role.ADMIN:
        return RedirectResponse(url="/", status_code=303)

    user_to_delete = db.query(User).filter(User.id == user_id).first()
    if user_to_delete:
        db.delete(user_to_delete)
        db.commit()

    return RedirectResponse(url="/admin/users", status_code=303)