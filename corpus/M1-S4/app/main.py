import os
from datetime import date, timedelta
from fastapi import FastAPI, Request, Depends, Form, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import func
import csv, io, shutil

from models import Base, engine, get_db, User, LeaveRequest, ROLE_ADMIN, ROLE_MANAGER, ROLE_EMPLOYEE, LEAVE_PENDING, LEAVE_APPROVED, LEAVE_REJECTED

app = FastAPI(title="PME Admin Dashboard")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        if db.query(User).count() == 0:
            seed_data(db)
    finally:
        db.close()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

def seed_data(db: Session):
    admin = User(first_name="Alice", last_name="Admin", email="admin@pme.local", password_hash=hash_password("admin123"), role=ROLE_ADMIN, department="Direction", salary=78000)
    m1 = User(first_name="Marc", last_name="Martin", email="marc@pme.local", password_hash=hash_password("manager123"), role=ROLE_MANAGER, department="Tech", salary=62000)
    m2 = User(first_name="Sofia", last_name="Durand", email="sofia@pme.local", password_hash=hash_password("manager123"), role=ROLE_MANAGER, department="RH", salary=60000)
    db.add_all([admin, m1, m2]); db.commit()
    for u in [admin, m1, m2]: db.refresh(u)
    employees = [
        User(first_name="Nina", last_name="Bernard", email="nina@pme.local", password_hash=hash_password("employee123"), role=ROLE_EMPLOYEE, department="Tech", salary=41000, manager_id=m1.id),
        User(first_name="Lucas", last_name="Petit", email="lucas@pme.local", password_hash=hash_password("employee123"), role=ROLE_EMPLOYEE, department="Tech", salary=43500, manager_id=m1.id),
        User(first_name="Emma", last_name="Robert", email="emma@pme.local", password_hash=hash_password("employee123"), role=ROLE_EMPLOYEE, department="Tech", salary=45000, manager_id=m1.id),
        User(first_name="Hugo", last_name="Moreau", email="hugo@pme.local", password_hash=hash_password("employee123"), role=ROLE_EMPLOYEE, department="RH", salary=39000, manager_id=m2.id),
        User(first_name="Léa", last_name="Leroy", email="lea@pme.local", password_hash=hash_password("employee123"), role=ROLE_EMPLOYEE, department="RH", salary=40500, manager_id=m2.id),
    ]
    db.add_all(employees); db.commit()
    for emp in employees[:3]: db.refresh(emp)
    db.add_all([
        LeaveRequest(user_id=employees[0].id, start_date=date.today()+timedelta(days=3), end_date=date.today()+timedelta(days=7), reason="Vacances", status=LEAVE_PENDING),
        LeaveRequest(user_id=employees[1].id, start_date=date.today()-timedelta(days=10), end_date=date.today()-timedelta(days=8), reason="Rendez-vous familial", status=LEAVE_APPROVED, reviewed_by_id=m1.id),
        LeaveRequest(user_id=employees[3].id, start_date=date.today()+timedelta(days=1), end_date=date.today()+timedelta(days=2), reason="Personnel", status=LEAVE_PENDING),
    ])
    db.commit()

def current_user(request: Request, db: Session):
    uid = request.cookies.get("user_id")
    if not uid: return None
    return db.query(User).filter(User.id == int(uid)).first()

def require_user(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user: raise HTTPException(status_code=307, headers={"Location": "/login"})
    return user

def require_role(user: User, *roles):
    if user.role not in roles: raise HTTPException(status_code=403, detail="Accès refusé")

def save_upload(file: UploadFile | None) -> str | None:
    if not file or not file.filename: return None
    safe = os.path.basename(file.filename).replace(" ", "_")
    filename = f"{int(__import__('time').time())}_{safe}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return f"/static/uploads/{filename}"

@app.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user: return RedirectResponse("/login")
    return RedirectResponse("/dashboard")

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Email ou mot de passe invalide"}, status_code=401)
    response = RedirectResponse("/dashboard", status_code=303)
    response.set_cookie("user_id", str(user.id), httponly=True, samesite="lax")
    return response

@app.get("/logout")
def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie("user_id")
    return response

@app.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)):
    if user.role == ROLE_ADMIN: return RedirectResponse("/admin/users")
    if user.role == ROLE_MANAGER: return RedirectResponse("/manager")
    leaves = db.query(LeaveRequest).filter(LeaveRequest.user_id == user.id).order_by(LeaveRequest.created_at.desc()).all()
    return templates.TemplateResponse("employee.html", {"request": request, "user": user, "leaves": leaves})

@app.post("/leave/request")
def request_leave(start_date: str = Form(...), end_date: str = Form(...), reason: str = Form(...), db: Session = Depends(get_db), user: User = Depends(require_user)):
    db.add(LeaveRequest(user_id=user.id, start_date=date.fromisoformat(start_date), end_date=date.fromisoformat(end_date), reason=reason))
    db.commit()
    return RedirectResponse("/dashboard", status_code=303)

@app.post("/profile/photo")
def profile_photo(photo: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(require_user)):
    path = save_upload(photo)
    user.profile_photo = path
    db.commit()
    return RedirectResponse("/dashboard", status_code=303)

@app.get("/manager")
def manager_view(request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)):
    require_role(user, ROLE_MANAGER, ROLE_ADMIN)
    team = db.query(User).filter(User.manager_id == user.id).all() if user.role == ROLE_MANAGER else db.query(User).filter(User.role != ROLE_ADMIN).all()
    team_ids = [u.id for u in team]
    leaves = db.query(LeaveRequest).filter(LeaveRequest.user_id.in_(team_ids)).order_by(LeaveRequest.created_at.desc()).all() if team_ids else []
    return templates.TemplateResponse("manager.html", {"request": request, "user": user, "team": team, "leaves": leaves})

@app.post("/manager/leave/{leave_id}")
def review_leave(leave_id: int, status: str = Form(...), manager_comment: str = Form(""), db: Session = Depends(get_db), user: User = Depends(require_user)):
    require_role(user, ROLE_MANAGER, ROLE_ADMIN)
    leave = db.query(LeaveRequest).get(leave_id)
    if not leave: raise HTTPException(404)
    if user.role == ROLE_MANAGER and leave.user.manager_id != user.id: raise HTTPException(403)
    leave.status = status if status in [LEAVE_APPROVED, LEAVE_REJECTED] else LEAVE_PENDING
    leave.manager_comment = manager_comment
    leave.reviewed_by_id = user.id
    db.commit()
    return RedirectResponse("/manager", status_code=303)

@app.get("/admin/users")
def admin_users(request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)):
    require_role(user, ROLE_ADMIN)
    users = db.query(User).order_by(User.department, User.last_name).all()
    managers = db.query(User).filter(User.role == ROLE_MANAGER).all()
    return templates.TemplateResponse("admin_users.html", {"request": request, "user": user, "users": users, "managers": managers, "roles": [ROLE_EMPLOYEE, ROLE_MANAGER, ROLE_ADMIN]})

@app.post("/admin/users/create")
def create_user(first_name: str = Form(...), last_name: str = Form(...), email: str = Form(...), password: str = Form(...), role: str = Form(...), department: str = Form(...), salary: float = Form(...), manager_id: str = Form(""), photo: UploadFile = File(None), db: Session = Depends(get_db), user: User = Depends(require_user)):
    require_role(user, ROLE_ADMIN)
    new_user = User(first_name=first_name, last_name=last_name, email=email, password_hash=hash_password(password), role=role, department=department, salary=salary, manager_id=int(manager_id) if manager_id else None, profile_photo=save_upload(photo))
    db.add(new_user); db.commit()
    return RedirectResponse("/admin/users", status_code=303)

@app.post("/admin/users/{uid}/edit")
def edit_user(uid: int, first_name: str = Form(...), last_name: str = Form(...), email: str = Form(...), role: str = Form(...), department: str = Form(...), salary: float = Form(...), manager_id: str = Form(""), password: str = Form(""), photo: UploadFile = File(None), db: Session = Depends(get_db), user: User = Depends(require_user)):
    require_role(user, ROLE_ADMIN)
    target = db.query(User).get(uid)
    if not target: raise HTTPException(404)
    target.first_name, target.last_name, target.email, target.role, target.department, target.salary = first_name, last_name, email, role, department, salary
    target.manager_id = int(manager_id) if manager_id else None
    if password: target.password_hash = hash_password(password)
    path = save_upload(photo)
    if path: target.profile_photo = path
    db.commit()
    return RedirectResponse("/admin/users", status_code=303)

@app.post("/admin/users/{uid}/delete")
def delete_user(uid: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    require_role(user, ROLE_ADMIN)
    if uid == user.id: raise HTTPException(400, "Impossible de supprimer le compte connecté")
    target = db.query(User).get(uid)
    if target:
        for teammate in db.query(User).filter(User.manager_id == uid).all(): teammate.manager_id = None
        db.delete(target); db.commit()
    return RedirectResponse("/admin/users", status_code=303)

@app.get("/admin/stats")
def stats(request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)):
    require_role(user, ROLE_ADMIN)
    dept_counts = db.query(User.department, func.count(User.id)).group_by(User.department).all()
    total_salaries = db.query(func.sum(User.salary)).scalar() or 0
    pending = db.query(LeaveRequest).filter(LeaveRequest.status == LEAVE_PENDING).count()
    approved_current = db.query(LeaveRequest).filter(LeaveRequest.status == LEAVE_APPROVED, LeaveRequest.start_date <= date.today(), LeaveRequest.end_date >= date.today()).count()
    avg_salary = db.query(func.avg(User.salary)).scalar() or 0
    return templates.TemplateResponse("stats.html", {"request": request, "user": user, "dept_counts": dept_counts, "total_salaries": total_salaries, "pending": pending, "approved_current": approved_current, "avg_salary": avg_salary})

@app.get("/admin/export.csv")
def export_csv(db: Session = Depends(get_db), user: User = Depends(require_user)):
    require_role(user, ROLE_ADMIN)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "prenom", "nom", "email", "role", "departement", "salaire", "manager"])
    for u in db.query(User).order_by(User.id).all():
        writer.writerow([u.id, u.first_name, u.last_name, u.email, u.role, u.department, u.salary, u.manager.full_name if u.manager else ""])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=employes.csv"})
