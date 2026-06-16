from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from models import User, LeaveRequest, Role
from main import get_db, templates, require_auth, UPLOAD_DIR
from datetime import date
import os
from werkzeug.utils import secure_filename

router = APIRouter(prefix="/employee", tags=["employee"])

@router.get("/dashboard", response_class=HTMLResponse)
async def employee_dashboard(request: Request, db: Session = Depends(get_db)):
    user = require_auth(request, db)
    if user.role != Role.EMPLOYEE:
        return RedirectResponse(url="/", status_code=303)

    leave_requests = db.query(LeaveRequest).filter(LeaveRequest.user_id == user.id).all()
    return templates.TemplateResponse(
        "employee/dashboard.html",
        {"request": request, "user": user, "leave_requests": leave_requests}
    )

@router.get("/profile", response_class=HTMLResponse)
async def employee_profile(request: Request, db: Session = Depends(get_db)):
    user = require_auth(request, db)
    if user.role != Role.EMPLOYEE:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("employee/profile.html", {"request": request, "user": user})

@router.get("/leave-request", response_class=HTMLResponse)
async def leave_request(request: Request, db: Session = Depends(get_db)):
    user = require_auth(request, db)
    if user.role != Role.EMPLOYEE:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("employee/leave_request.html", {"request": request, "user": user})

@router.post("/leave-request")
async def submit_leave_request(request: Request, db: Session = Depends(get_db)):
    user = require_auth(request, db)
    if user.role != Role.EMPLOYEE:
        return RedirectResponse(url="/", status_code=303)

    form_data = await request.form()
    start_date = form_data.get("start_date")
    end_date = form_data.get("end_date")
    reason = form_data.get("reason")

    leave_request = LeaveRequest(
        user_id=user.id,
        start_date=date.fromisoformat(start_date),
        end_date=date.fromisoformat(end_date),
        reason=reason,
    )
    db.add(leave_request)
    db.commit()

    return RedirectResponse(url="/employee/dashboard", status_code=303)

@router.post("/upload-profile-picture")
async def upload_profile_picture(request: Request, db: Session = Depends(get_db)):
    user = require_auth(request, db)
    form_data = await request.form()
    file = form_data.get("profile_picture")

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_DIR, f"user_{user.id}_{filename}")
        with open(file_path, "wb") as f:
            f.write(await file.read())

        user.profile_picture = f"/static/uploads/{os.path.basename(file_path)}"
        db.commit()

    return RedirectResponse(url="/employee/profile", status_code=303)