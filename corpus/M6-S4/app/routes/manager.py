from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from models import (
    SessionLocal,
    User,
    LeaveRequest,
    LEAVE_APPROVED,
    LEAVE_REJECTED,
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


def manager_required(user: User):
    if not user or user.role not in ("manager", "admin"):
        raise PermissionError


@router.get("/manager/leaves")
def manager_leaves(
    request: Request, db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    manager_required(user)

    team_ids = [m.id for m in user.team_members]
    leaves = (
        db.query(LeaveRequest)
        .filter(LeaveRequest.employee_id.in_(team_ids))
        .order_by(LeaveRequest.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        "manager_leaves.html",
        {"request": request, "user": user, "leaves": leaves},
    )


@router.post("/manager/leaves/decision")
def manager_decide_leave(
    request: Request,
    leave_id: int = Form(...),
    decision: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    manager_required(user)

    leave = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not leave:
        return RedirectResponse("/manager/leaves", status_code=303)

    if decision == "approve":
        leave.status = LEAVE_APPROVED
    elif decision == "reject":
        leave.status = LEAVE_REJECTED
    db.commit()
    return RedirectResponse("/manager/leaves", status_code=303)
