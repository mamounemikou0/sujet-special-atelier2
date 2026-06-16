from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from models import Base, engine, SessionLocal, User
from routes import auth, users
from routes.auth import get_password_hash

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialisation de la base de données au démarrage
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Création du compte admin s'il n'existe pas
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        new_admin = User(
            email="admin@admin.com",
            username="admin",
            hashed_password=get_password_hash("admin123"),
            is_admin=True
        )
        db.add(new_admin)
        db.commit()
    db.close()
    yield

app = FastAPI(lifespan=lifespan)

# Montage des fichiers statiques et des templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Inclusion des routeurs API
app.include_router(auth.router)
app.include_router(users.router)

# Routes Frontend (Rendu HTML)
@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})