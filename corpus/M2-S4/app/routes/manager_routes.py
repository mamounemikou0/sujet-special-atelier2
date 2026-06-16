from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from templates_config import Templates as Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models import User, LeaveRequest, LeaveStatusEnum
from auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def require_manager(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role.value not in ("manager", "admin"):
        raise HTTPException(status_code=403, detail="Accès refusé")
    return current_user


@router.get("/manager/dashboard", response_class=HTMLResponse)
async def manager_dashboard(request: Request, current_user: User = Depends(require_manager), db: Session = Depends(get_db)):
    team = db.query(User).filter(User.manager_id == current_user.id).all()
    team_ids = [m.id for m in team]
    pending_leaves = db.query(LeaveRequest).filter(
        LeaveRequest.user_id.in_(team_ids),
        LeaveRequest.status == LeaveStatusEnum.pending
    ).all()
    return templates.TemplateResponse("manager/dashboard.html", {
        "request": request,
        "user": current_user,
        "team": team,
        "pending_leaves": pending_leaves,
    })


@router.get("/manager/leaves", response_class=HTMLResponse)
async def manager_leaves(request: Request, current_user: User = Depends(require_manager), db: Session = Depends(get_db)):
    team = db.query(User).filter(User.manager_id == current_user.id).all()
    team_ids = [m.id for m in team]
    leaves = db.query(LeaveRequest).filter(
        LeaveRequest.user_id.in_(team_ids)
    ).order_by(LeaveRequest.created_at.desc()).all()
    # Attach user info
    users_map = {u.id: u for u in team}
    return templates.TemplateResponse("manager/leaves.html", {
        "request": request,
        "user": current_user,
        "leaves": leaves,
        "users_map": users_map,
    })


@router.post("/manager/leaves/{leave_id}/action")
async def action_leave(
    leave_id: int,
    action: str = Form(...),
    comment: str = Form(""),
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
):
    leave = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Demande introuvable")
    # Verify the leave belongs to manager's team
    team_ids = [u.id for u in db.query(User).filter(User.manager_id == current_user.id).all()]
    if leave.user_id not in team_ids and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")
    if action == "approve":
        leave.status = LeaveStatusEnum.approved
    elif action == "refuse":
        leave.status = LeaveStatusEnum.refused
    else:
        raise HTTPException(status_code=400, detail="Action invalide")
    leave.manager_comment = comment
    db.commit()
    return RedirectResponse(url="/manager/leaves?success=1", status_code=302)


@router.get("/manager/team", response_class=HTMLResponse)
async def manager_team(request: Request, current_user: User = Depends(require_manager), db: Session = Depends(get_db)):
    team = db.query(User).filter(User.manager_id == current_user.id).all()
    return templates.TemplateResponse("manager/team.html", {
        "request": request,
        "user": current_user,
        "team": team,
    })
