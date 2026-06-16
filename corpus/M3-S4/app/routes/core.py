import os
import csv
import shutil
import hashlib
from io import StringIO
from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from models import SessionLocal, User, LeaveRequest
from jose import jwt

router = APIRouter()
templates = Jinja2Templates(directory="templates")

SECRET_KEY = "supersecretkeyfortoken"
ALGORITHM = "HS256"

def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        db = SessionLocal()
        user = db.query(User).filter(User.id == payload["user_id"]).first()
        db.close()
        return user
    except:
        return None

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    db = SessionLocal()
    context = {"request": request, "user": user}

    if user.role == "Employé":
        context["leaves"] = db.query(LeaveRequest).filter(LeaveRequest.user_id == user.id).all()
    elif user.role == "Manager":
        context["leaves"] = db.query(LeaveRequest).filter(LeaveRequest.user_id == user.id).all()
        team = db.query(User).filter(User.manager_id == user.id).all()
        context["team"] = team
        team_ids = [u.id for u in team]
        context["team_leaves"] = db.query(LeaveRequest).filter(LeaveRequest.user_id.in_(team_ids)).all() if team_ids else []
    elif user.role == "Admin":
        context["all_users"] = db.query(User).all()
        context["all_leaves"] = db.query(LeaveRequest).all()
        context["managers"] = db.query(User).filter(User.role == "Manager").all()

    db.close()
    return templates.TemplateResponse("dashboard.html", context)

@router.post("/leave/request")
def request_leave(request: Request, start_date: str = Form(...), end_date: str = Form(...), reason: str = Form(...)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    db = SessionLocal()
    new_leave = LeaveRequest(user_id=user.id, start_date=start_date, end_date=end_date, reason=reason, status="En attente")
    db.add(new_leave)
    db.commit()
    db.close()
    return RedirectResponse(url="/dashboard", status_code=303)

@router.post("/leave/action/{leave_id}")
def leave_action(request: Request, leave_id: int, action: str = Form(...)):
    user = get_current_user(request)
    if not user or user.role not in ["Manager", "Admin"]:
        return RedirectResponse(url="/", status_code=303)
    db = SessionLocal()
    leave = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if leave:
        leave.status = "Approuvé" if action == "approve" else "Refusé"
        db.commit()
    db.close()
    return RedirectResponse(url="/dashboard", status_code=303)

@router.post("/profile/upload")
async def upload_profile_pic(request: Request, file: UploadFile = File(...)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    if file.filename:
        ext = os.path.splitext(file.filename)[1]
        filename = f"user_{user.id}{ext}"
        filepath = os.path.join("static", "uploads", filename)
        
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        db = SessionLocal()
        db_user = db.query(User).filter(User.id == user.id).first()
        db_user.profile_pic = filename
        db.commit()
        db.close()
        
    return RedirectResponse(url="/dashboard", status_code=303)

@router.post("/admin/user/create")
def create_user(request: Request, email: str = Form(...), name: str = Form(...), password: str = Form(...), role: str = Form(...), department: str = Form(...), salary: float = Form(...), manager_id: str = Form(None)):
    user = get_current_user(request)
    if not user or user.role != "Admin":
        return RedirectResponse(url="/", status_code=303)
    
    db = SessionLocal()
    hashed = hashlib.sha256(password.encode()).hexdigest()
    m_id = int(manager_id) if manager_id and manager_id.isdigit() else None
    new_user = User(email=email, name=name, hashed_password=hashed, role=role, department=department, salary=salary, manager_id=m_id)
    db.add(new_user)
    db.commit()
    db.close()
    return RedirectResponse(url="/dashboard", status_code=303)

@router.post("/admin/user/update/{user_id}")
def update_user(request: Request, user_id: int, email: str = Form(...), name: str = Form(...), role: str = Form(...), department: str = Form(...), salary: float = Form(...), manager_id: str = Form(None)):
    user = get_current_user(request)
    if not user or user.role != "Admin":
        return RedirectResponse(url="/", status_code=303)
    
    db = SessionLocal()
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db_user.email = email
        db_user.name = name
        db_user.role = role
        db_user.department = department
        db_user.salary = salary
        db_user.manager_id = int(manager_id) if manager_id and manager_id.isdigit() else None
        db.commit()
    db.close()
    return RedirectResponse(url="/dashboard", status_code=303)

@router.post("/admin/user/delete/{user_id}")
def delete_user(request: Request, user_id: int):
    user = get_current_user(request)
    if not user or user.role != "Admin":
        return RedirectResponse(url="/", status_code=303)
    
    db = SessionLocal()
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    db.close()
    return RedirectResponse(url="/dashboard", status_code=303)

@router.get("/admin/stats", response_class=HTMLResponse)
def view_stats(request: Request):
    user = get_current_user(request)
    if not user or user.role != "Admin":
        return RedirectResponse(url="/", status_code=303)
    
    db = SessionLocal()
    users = db.query(User).all()
    leaves = db.query(LeaveRequest).all()
    
    total_salaries = sum(u.salary for u in users)
    active_leaves = sum(1 for l in leaves if l.status == "Approuvé")
    pending_leaves = sum(1 for l in leaves if l.status == "En attente")
    
    dept_counts = {}
    for u in users:
        dept_counts[u.department] = dept_counts.get(u.department, 0) + 1
        
    db.close()
    
    return templates.TemplateResponse("stats.html", {
        "request": request,
        "user": user,
        "total_employees": len(users),
        "total_salaries": total_salaries,
        "active_leaves": active_leaves,
        "pending_leaves": pending_leaves,
        "dept_counts": dept_counts
    })

@router.get("/admin/export/csv")
def export_csv(request: Request):
    user = get_current_user(request)
    if not user or user.role != "Admin":
        return RedirectResponse(url="/", status_code=303)
    
    db = SessionLocal()
    users = db.query(User).all()
    db.close()
    
    stream = StringIO()
    writer = csv.writer(stream)
    writer.writerow(["ID", "Nom", "Email", "Role", "Departement", "Salaire"])
    
    for u in users:
        writer.writerow([u.id, u.name, u.email, u.role, u.department, u.salary])
        
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=employes.csv"
    return response