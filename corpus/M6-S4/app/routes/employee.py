from datetime import date

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from models import (
    SessionLocal,
    User,
    LeaveRequest,
    LEAVE_PENDING,
)
from .auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def employee_required(user: User):
    if not user or user.role not in ("employee", "manager", "admin"):
        # on laisse aussi manager/admin accéder à leur propre vue employé
        raise PermissionError


@router.get("/employee/profile")
def employee_profile(
    request: Request, db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    employee_required(user)
    leaves = (
        db.query(LeaveRequest)
        .filter(LeaveRequest.employee_id == user.id)
        .order_by(LeaveRequest.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        "employee_profile.html",
        {"request": request, "user": user, "leaves": leaves},
    )


@router.post("/employee/leave/request")
def request_leave(
    request: Request,
    start_date: str = Form(...),
    end_date: str = Form(...),
    reason: str = Form(""),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    employee_required(user)

    try:
        sd = date.fromisoformat(start_date)
        ed = date.fromisoformat(end_date)
    except ValueError:
        return RedirectResponse(
            "/employee/profile?error=dates", status_code=303
        )

    leave = LeaveRequest(
        employee_id=user.id,
        manager_id=user.manager_id,
        start_date=sd,
        end_date=ed,
        reason=reason,
        status=LEAVE_PENDING,
    )
    db.add(leave)
    db.commit()
    return RedirectResponse("/employee/profile", status_code=303)
