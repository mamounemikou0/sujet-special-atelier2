import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from models import init_db
from routes import auth, dashboard, admin, manager, employee

app = FastAPI()

# Session (clé simple pour dev)
app.add_middleware(SessionMiddleware, secret_key="dev-secret-key")

# Static
os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Routes
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(admin.router)
app.include_router(manager.router)
app.include_router(employee.router)


@app.on_event("startup")
def on_startup():
    init_db()
