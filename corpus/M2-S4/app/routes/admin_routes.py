import csv
import io
import os
import shutil
import uuid
from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from templates_config import Templates as Jinja2Templates
from sqlalchemy.orm import Session

from auth import get_current_user, hash_password
from database import get_db
from models import LeaveRequest, LeaveStatusEnum, RoleEnum, User

router = APIRouter()
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")
    return current_user


@router.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    total_users = db.query(User).count()
    total_employees = db.query(User).filter(User.role == RoleEnum.employee).count()
    total_managers = db.query(User).filter(User.role == RoleEnum.manager).count()
    pending_leaves = db.query(LeaveRequest).filter(LeaveRequest.status == LeaveStatusEnum.pending).count()
    total_salary = db.query(User).all()
    salary_sum = sum(u.salary for u in total_salary)
    recent_users = db.query(User).order_by(User.created_at.desc()).limit(5).all()
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "user": current_user,
            "total_users": total_users,
            "total_employees": total_employees,
            "total_managers": total_managers,
            "pending_leaves": pending_leaves,
            "salary_sum": salary_sum,
            "recent_users": recent_users,
        },
    )


@router.get("/admin/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.full_name).all()
    managers = db.query(User).filter(User.role.in_([RoleEnum.manager, RoleEnum.admin])).all()
    return templates.TemplateResponse(
        "admin/users.html",
        {"request": request, "user": current_user, "users": users, "managers": managers},
    )


@router.post("/admin/users/create")
async def admin_create_user(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    department: str = Form(""),
    position: str = Form(""),
    salary: float = Form(0.0),
    phone: str = Form(""),
    hire_date: str = Form(""),
    manager_id: str = Form(""),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return RedirectResponse(url="/admin/users?error=email", status_code=302)
    new_user = User(
        full_name=full_name,
        email=email,
        hashed_password=hash_password(password),
        role=RoleEnum(role),
        department=department or None,
        position=position or None,
        salary=salary,
        phone=phone or None,
        hire_date=date.fromisoformat(hire_date) if hire_date else None,
        manager_id=int(manager_id) if manager_id else None,
    )
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/admin/users?success=created", status_code=302)


@router.get("/admin/users/{user_id}/edit", response_class=HTMLResponse)
async def admin_edit_user_page(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404)
    managers = db.query(User).filter(User.role.in_([RoleEnum.manager, RoleEnum.admin])).all()
    return templates.TemplateResponse(
        "admin/edit_user.html",
        {"request": request, "user": current_user, "target": target, "managers": managers},
    )


@router.post("/admin/users/{user_id}/edit")
async def admin_edit_user(
    user_id: int,
    full_name: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    department: str = Form(""),
    position: str = Form(""),
    salary: float = Form(0.0),
    phone: str = Form(""),
    hire_date: str = Form(""),
    manager_id: str = Form(""),
    new_password: str = Form(""),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404)
    # Check email uniqueness
    conflict = db.query(User).filter(User.email == email, User.id != user_id).first()
    if conflict:
        return RedirectResponse(url=f"/admin/users/{user_id}/edit?error=email", status_code=302)
    target.full_name = full_name
    target.email = email
    target.role = RoleEnum(role)
    target.department = department or None
    target.position = position or None
    target.salary = salary
    target.phone = phone or None
    target.hire_date = date.fromisoformat(hire_date) if hire_date else None
    target.manager_id = int(manager_id) if manager_id else None
    if new_password:
        target.hashed_password = hash_password(new_password)
    db.commit()
    return RedirectResponse(url="/admin/users?success=updated", status_code=302)


@router.post("/admin/users/{user_id}/upload-photo")
async def admin_upload_photo(
    user_id: int,
    photo: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404)
    ext = os.path.splitext(photo.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
        return RedirectResponse(url=f"/admin/users/{user_id}/edit?error=format", status_code=302)
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(photo.file, f)
    if target.profile_picture:
        old_path = os.path.join(UPLOAD_DIR, target.profile_picture)
        if os.path.exists(old_path):
            os.remove(old_path)
    target.profile_picture = filename
    db.commit()
    return RedirectResponse(url=f"/admin/users/{user_id}/edit?success=photo", status_code=302)


@router.post("/admin/users/{user_id}/delete")
async def admin_delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404)
    if target.id == current_user.id:
        return RedirectResponse(url="/admin/users?error=self", status_code=302)
    db.query(LeaveRequest).filter(LeaveRequest.user_id == target.id).delete()
    if target.profile_picture:
        old_path = os.path.join(UPLOAD_DIR, target.profile_picture)
        if os.path.exists(old_path):
            os.remove(old_path)
    db.delete(target)
    db.commit()
    return RedirectResponse(url="/admin/users?success=deleted", status_code=302)


@router.get("/admin/salaries", response_class=HTMLResponse)
async def admin_salaries(
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.department, User.full_name).all()
    return templates.TemplateResponse(
        "admin/salaries.html", {"request": request, "user": current_user, "users": users}
    )


@router.get("/admin/stats", response_class=HTMLResponse)
async def admin_stats(
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    all_users = db.query(User).all()
    # Employees by department
    dept_counts: dict = {}
    dept_salaries: dict = {}
    for u in all_users:
        dept = u.department or "Non assigné"
        dept_counts[dept] = dept_counts.get(dept, 0) + 1
        dept_salaries[dept] = dept_salaries.get(dept, 0.0) + u.salary

    total_salary = sum(u.salary for u in all_users)
    total_employees = db.query(User).filter(User.role == RoleEnum.employee).count()
    total_managers = db.query(User).filter(User.role == RoleEnum.manager).count()

    today = date.today()
    active_leaves = db.query(LeaveRequest).filter(
        LeaveRequest.status == LeaveStatusEnum.approved,
        LeaveRequest.start_date <= today,
        LeaveRequest.end_date >= today,
    ).count()
    pending_leaves = db.query(LeaveRequest).filter(LeaveRequest.status == LeaveStatusEnum.pending).count()
    approved_leaves = db.query(LeaveRequest).filter(LeaveRequest.status == LeaveStatusEnum.approved).count()
    refused_leaves = db.query(LeaveRequest).filter(LeaveRequest.status == LeaveStatusEnum.refused).count()

    return templates.TemplateResponse(
        "admin/stats.html",
        {
            "request": request,
            "user": current_user,
            "dept_counts": dept_counts,
            "dept_salaries": dept_salaries,
            "total_salary": total_salary,
            "total_employees": total_employees,
            "total_managers": total_managers,
            "active_leaves": active_leaves,
            "pending_leaves": pending_leaves,
            "approved_leaves": approved_leaves,
            "refused_leaves": refused_leaves,
        },
    )


@router.get("/admin/export/csv")
async def export_csv(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.full_name).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Nom", "Email", "Rôle", "Département", "Poste", "Salaire", "Téléphone", "Date embauche"])
    for u in users:
        writer.writerow([
            u.id, u.full_name, u.email, u.role.value,
            u.department or "", u.position or "", f"{u.salary:.2f}",
            u.phone or "", u.hire_date.isoformat() if u.hire_date else "",
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=employes.csv"},
    )
