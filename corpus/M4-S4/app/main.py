from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, LeaveRequest, Role, Department
from datetime import datetime, date
import os
import shutil
from passlib.context import CryptContext
from typing import Optional

# Initialisation de l'application
app = FastAPI()

# Configuration de la base de données
DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Création des tables
Base.metadata.create_all(bind=engine)

# Dossier pour les uploads
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Configuration des templates et des fichiers statiques
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Contexte pour le hachage des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Import des routes
from routes import auth, employees, managers, admins, stats

app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(managers.router)
app.include_router(admins.router)
app.include_router(stats.router)

# Middleware pour vérifier la session
from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from typing import Optional

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request, db=Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()

def require_auth(request: Request, db=Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return user

def require_role(role: Role):
    def wrapper(request: Request, db=Depends(get_db)):
        user = require_auth(request, db)
        if user.role != role:
            raise HTTPException(status_code=403, detail="Accès refusé")
        return user
    return wrapper

# Injection des données d'exemple
def inject_sample_data():
    db = SessionLocal()
    if db.query(User).count() == 0:
        # Création des utilisateurs
        admin = User(
            email="admin@pme.com",
            hashed_password=pwd_context.hash("admin123"),
            full_name="Admin PME",
            role=Role.ADMIN,
            department=Department.IT,
            salary=8000.0,
        )
        db.add(admin)

        manager1 = User(
            email="manager1@pme.com",
            hashed_password=pwd_context.hash("manager123"),
            full_name="Manager IT",
            role=Role.MANAGER,
            department=Department.IT,
            salary=6000.0,
            manager_id=admin.id,
        )
        db.add(manager1)

        manager2 = User(
            email="manager2@pme.com",
            hashed_password=pwd_context.hash("manager123"),
            full_name="Manager RH",
            role=Role.MANAGER,
            department=Department.HR,
            salary=5500.0,
            manager_id=admin.id,
        )
        db.add(manager2)

        employees = [
            User(
                email=f"employee{i}@pme.com",
                hashed_password=pwd_context.hash("employee123"),
                full_name=f"Employé {i}",
                role=Role.EMPLOYEE,
                department=Department.IT if i < 3 else Department.HR,
                salary=3000.0 + i * 500,
                manager_id=manager1.id if i < 3 else manager2.id,
            )
            for i in range(1, 6)
        ]
        db.add_all(employees)

        # Création de demandes de congés
        leave_requests = [
            LeaveRequest(
                user_id=employees[0].id,
                start_date=date(2026, 7, 1),
                end_date=date(2026, 7, 5),
                reason="Congé d'été",
            ),
            LeaveRequest(
                user_id=employees[1].id,
                start_date=date(2026, 7, 10),
                end_date=date(2026, 7, 15),
                reason="Congé familial",
            ),
        ]
        db.add_all(leave_requests)

        db.commit()
    db.close()

# Appel de l'injection des données au démarrage
@app.on_event("startup")
async def startup_event():
    inject_sample_data()

# Route pour la page d'accueil
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})