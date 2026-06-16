from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from models import User, LeaveRequest, Role
from main import get_db, templates, require_auth

router = APIRouter(prefix="/manager", tags=["manager"])

@router.get("/dashboard", response_class=HTMLResponse)
async def manager_dashboard(request: Request, db: Session = Depends(get_db)):
    user = require_auth(request, db)
    if user.role != Role.MANAGER:
        return RedirectResponse(url="/", status_code=303)

    team = db.query(User).filter(User.manager_id == user.id).all()
    leave_requests = db.query(LeaveRequest).filter(LeaveRequest.user_id.in_([u.id for u in team])).all()

    return templates.TemplateResponse(
        "manager/dashboard.html",
        {"request": request, "user": user, "team": team, "leave_requests": leave_requests}
    )

@router.get("/team", response_class=HTMLResponse)
async def manager_team(request: Request, db: Session = Depends(get_db)):
    user = require_auth(request, db)
    if user.role != Role.MANAGER:
        return RedirectResponse(url="/", status_code=303)

    team = db.query(User).filter(User.manager_id == user.id).all()
    return templates.TemplateResponse("manager/team.html", {"request": request, "user": user, "team": team})

@router.get("/leave-approvals", response_class=HTMLResponse)
async def manager_leave_approvals(request: Request, db: Session = Depends(get_db)):
    user = require_auth(request, db)
    if user.role != Role.MANAGER:
        return RedirectResponse(url="/", status_code=303)

    team = db.query(User).filter(User.manager_id == user.id).all()
    leave_requests = db.query(LeaveRequest).filter(
        LeaveRequest.user_id.in_([u.id for u in team]),
        LeaveRequest.status == "En attente"
    ).all()

    return templates.TemplateResponse(
        "manager/leave_approvals.html",
        {"request": request, "user": user, "leave_requests": leave_requests}
    )

@router.post("/approve-leave/{leave_id}")
async def approve_leave(leave_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_auth(request, db)
    if user.role != Role.MANAGER:
        return RedirectResponse(url="/", status_code=303)

    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if leave_request:
        leave_request.status = "Approuvé"
        db.commit()

    return RedirectResponse(url="/manager/leave-approvals", status_code=303)

@router.post("/reject-leave/{leave_id}")
async def reject_leave(leave_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_auth(request, db)
    if user.role != Role.MANAGER:
        return RedirectResponse(url="/", status_code=303)

    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if leave_request:
        leave_request.status = "Refusé"
        db.commit()

    return RedirectResponse(url="/manager/leave-approvals", status_code=303)