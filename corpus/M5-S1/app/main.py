from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from models import init_db
from routes import auth, users

app = FastAPI(title="Gestion Utilisateurs")

# Monter les fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Initialiser la base de données au démarrage
@app.on_event("startup")
async def startup_event():
    init_db()

# Inclure les routes
app.include_router(auth.router)
app.include_router(users.router)

@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/login")