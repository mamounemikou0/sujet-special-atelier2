from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from models import User, LeaveRequest, Role, Department
from main import get_db, templates, require_auth
from sqlalchemy import func
from collections import defaultdict

router = APIRouter(prefix="/admin/stats", tags=["stats"])

@router.get("/", response_class=HTMLResponse)
async def admin_stats(request: Request, db: Session = Depends(get_db)):
    user = require_auth(request, db)
    if user.role != Role.ADMIN:
        return RedirectResponse(url="/", status_code=303)

    # Nombre d'employés par département
    dept_counts = db.query(
        User.department,
        func.count(User.id).label("count")
    ).group_by(User.department).all()

    dept_counts_dict = {d.value: count for d, count in dept_counts}

    # Total des salaires
    total_salary = db.query(func.sum(User.salary)).scalar() or 0

    # Congés en cours
    pending_leaves = db.query(LeaveRequest).filter(LeaveRequest.status == "En attente").count()
    approved_leaves = db.query(LeaveRequest).filter(LeaveRequest.status == "Approuvé").count()
    rejected_leaves = db.query(LeaveRequest).filter(LeaveRequest.status == "Refusé").count()

    # Salaires par département
    dept_salaries = db.query(
        User.department,
        func.sum(User.salary).label("total_salary")
    ).group_by(User.department).all()

    dept_salaries_dict = {d.value: total for d, total in dept_salaries}

    return templates.TemplateResponse(
        "admin/stats.html",
        {
            "request": request,
            "user": user,
            "dept_counts": dept_counts_dict,
            "total_salary": total_salary,
            "pending_leaves": pending_leaves,
            "approved_leaves": approved_leaves,
            "rejected_leaves": rejected_leaves,
            "dept_salaries": dept_salaries_dict,
        }
    )