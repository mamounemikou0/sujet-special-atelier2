import csv
import os
from io import StringIO
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Request,
    UploadFile,
)
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from models import (
    SessionLocal,
    User,
    LeaveRequest,
)
from .auth import get_current_user, hash_password

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def admin_required(user: User):
    if not user or user.role != "admin":
        raise PermissionError


@router.get("/admin/users")
def admin_users(
    request: Request, db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    admin_required(user)

    users = db.query(User).order_by(User.id).all()
    return templates.TemplateResponse(
        "admin_users.html",
        {"request": request, "user": user, "users": users},
    )


@router.post("/admin/users/create")
def admin_create_user(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    department: str = Form(""),
    salary: float = Form(0.0),
    manager_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    admin_required(user)

    new_user = User(
        full_name=full_name,
        email=email,
        password_hash=hash_password(password),
        role=role,
        department=department or None,
        salary=salary,
        manager_id=manager_id,
    )
    db.add(new_user)
    db.commit()
    return RedirectResponse("/admin/users", status_code=303)


@router.post("/admin/users/update")
def admin_update_user(
    request: Request,
    user_id: int = Form(...),
    full_name: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    department: str = Form(""),
    salary: float = Form(0.0),
    manager_id: Optional[int] = Form(None),
    password: str = Form(""),
    db: Session = Depends(get_db),
):
    current = get_current_user(request, db)
    if not current:
        return RedirectResponse("/login", status_code=303)
    admin_required(current)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return RedirectResponse("/admin/users", status_code=303)

    user.full_name = full_name
    user.email = email
    user.role = role
    user.department = department or None
    user.salary = salary
    user.manager_id = manager_id
    if password:
        user.password_hash = hash_password(password)
    db.commit()
    return RedirectResponse("/admin/users", status_code=303)


@router.post("/admin/users/delete")
def admin_delete_user(
    request: Request,
    user_id: int = Form(...),
    db: Session = Depends(get_db),
):
    current = get_current_user(request, db)
    if not current:
        return RedirectResponse("/login", status_code=303)
    admin_required(current)

    if current.id == user_id:
        return RedirectResponse("/admin/users", status_code=303)

    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
    return RedirectResponse("/admin/users", status_code=303)


@router.get("/admin/export_csv")
def admin_export_csv(
    request: Request, db: Session = Depends(get_db)
):
    current = get_current_user(request, db)
    if not current:
        return RedirectResponse("/login", status_code=303)
    admin_required(current)

    users = (
        db.query(User)
        .filter(User.role == "employee")
        .order_by(User.id)
        .all()
    )

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["id", "full_name", "email", "department", "salary", "manager_id"]
    )
    for u in users:
        writer.writerow(
            [
                u.id,
                u.full_name,
                u.email,
                u.department or "",
                u.salary,
                u.manager_id or "",
            ]
        )
    output.seek(0)
    headers = {
        "Content-Disposition": 'attachment; filename="employees.csv"'
    }
    return StreamingResponse(
        output, media_type="text/csv", headers=headers
    )


@router.get("/admin/stats")
def admin_stats(
    request: Request, db: Session = Depends(get_db)
):
    current = get_current_user(request, db)
    if not current:
        return RedirectResponse("/login", status_code=303)
    admin_required(current)

    # nombre d'employés par département
    dept_counts = (
        db.query(User.department, func.count(User.id))
        .filter(User.role == "employee")
        .group_by(User.department)
        .all()
    )

    # total des salaires
    total_salaries = (
        db.query(func.sum(User.salary))
        .filter(User.role == "employee")
        .scalar()
        or 0
    )

    # congés en cours (status approved et date >= aujourd'hui)
    from datetime import date as dt_date

    today = dt_date.today()
    ongoing_leaves = (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.status == "approved",
            LeaveRequest.end_date >= today,
        )
        .count()
    )

    return templates.TemplateResponse(
        "admin_stats.html",
        {
            "request": request,
            "user": current,
            "dept_counts": dept_counts,
            "total_salaries": total_salaries,
            "ongoing_leaves": ongoing_leaves,
        },
    )


@router.post("/profile/photo")
async def upload_profile_photo(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    current = get_current_user(request, db)
    if not current:
        return RedirectResponse("/login", status_code=303)

    uploads_dir = os.path.join("static", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    filename = f"user_{current.id}_{file.filename}"
    filepath = os.path.join(uploads_dir, filename)

    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)

    current.photo_filename = filename
    db.commit()
    return RedirectResponse("/employee/profile", status_code=303)
