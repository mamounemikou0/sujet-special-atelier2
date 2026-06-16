import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from models import init_db, SessionLocal, User
from routes import auth, catalog, cart, admin

app = FastAPI(title="Ma Petite Boutique FastAPI")

# Initialisation automatique de la base de données SQLite et des données
init_db()

# Création et montage des dossiers statiques
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Middleware global pour intercepter l'utilisateur connecté via cookie
@app.middleware("http")
async def add_user_to_request(request: Request, call_next):
    db = SessionLocal()
    user_id = request.cookies.get("user_id")
    request.state.user = None
    if user_id:
        try:
            request.state.user = db.query(User).filter(User.id == int(user_id)).first()
        except Exception:
            pass
    db.close()
    response = await call_next(request)
    return response

# Enregistrement des modules de routes
app.include_router(auth.router)
app.include_router(catalog.router)
app.include_router(cart.router)
app.include_router(admin.router)

@app.get("/")
def root():
    return RedirectResponse(url="/catalog")