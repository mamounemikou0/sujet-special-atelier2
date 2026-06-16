import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from models import init_db
from routes import auth, core

app = FastAPI(title="PME Dashboard System")

# S'assurer que les répertoires nécessaires existent au démarrage
os.makedirs("static/uploads", exist_ok=True)

# Initialisation de la BDD SQLite et injection des comptes
init_db()

# Montage du dossier static pour servir le CSS & les uploads d'images
app.mount("/static", StaticFiles(directory="static"), name="static")

# Inclusion des fichiers de routage
app.include_router(auth.router)
app.include_router(core.router)