from fastapi import APIRouter, Depends, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from templates_config import Templates as Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models import User, LeaveRequest, LeaveStatusEnum
from auth import get_current_user
from datetime import date
import os
import uuid
import shutil

router = APIRouter()
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    role = current_user.role.value
    if role == "admin":
        return RedirectResponse(url="/admin/dashboard", status_code=302)
    elif role == "manager":
        return RedirectResponse(url="/manager/dashboard", status_code=302)
    else:
        return RedirectResponse(url="/employee/profile", status_code=302)


# ─── Employee routes ────────────────────────────────────────────────────────

@router.get("/employee/profile", response_class=HTMLResponse)
async def employee_profile(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role.value != "employee":
        return RedirectResponse(url="/dashboard", status_code=302)
    manager = db.query(User).filter(User.id == current_user.manager_id).first() if current_user.manager_id else None
    return templates.TemplateResponse("employee/profile.html", {
        "request": request,
        "user": current_user,
        "manager": manager,
    })


@router.post("/employee/profile/upload-photo", response_class=HTMLResponse)
async def upload_profile_photo(
    request: Request,
    photo: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role.value != "employee":
        raise HTTPException(status_code=403, detail="Accès refusé")
    ext = os.path.splitext(photo.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
        return RedirectResponse(url="/employee/profile?error=format", status_code=302)
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(photo.file, f)
    if current_user.profile_picture:
        old_path = os.path.join(UPLOAD_DIR, current_user.profile_picture)
        if os.path.exists(old_path):
            os.remove(old_path)
    current_user.profile_picture = filename
    db.commit()
    return RedirectResponse(url="/employee/profile?success=photo", status_code=302)


@router.get("/employee/leaves", response_class=HTMLResponse)
async def employee_leaves(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role.value != "employee":
        return RedirectResponse(url="/dashboard", status_code=302)
    leaves = db.query(LeaveRequest).filter(LeaveRequest.user_id == current_user.id).order_by(LeaveRequest.created_at.desc()).all()
    return templates.TemplateResponse("employee/leaves.html", {
        "request": request,
        "user": current_user,
        "leaves": leaves,
        "today": date.today().isoformat(),
    })


@router.post("/employee/leaves/request")
async def request_leave(
    request: Request,
    start_date: str = Form(...),
    end_date: str = Form(...),
    reason: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role.value != "employee":
        raise HTTPException(status_code=403, detail="Accès refusé")
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError:
        return RedirectResponse(url="/employee/leaves?error=dates", status_code=302)
    if end < start:
        return RedirectResponse(url="/employee/leaves?error=dates", status_code=302)
    leave = LeaveRequest(
        user_id=current_user.id,
        manager_id=current_user.manager_id,
        start_date=start,
        end_date=end,
        reason=reason,
        status=LeaveStatusEnum.pending,
    )
    db.add(leave)
    db.commit()
    return RedirectResponse(url="/employee/leaves?success=1", status_code=302)
