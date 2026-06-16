from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from models import Base, engine, SessionLocal, User
from passlib.context import CryptContext
from routes import auth, users

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(title="Gestionnaire d'Utilisateurs")

# Session middleware (secret key for signing)
app.add_middleware(SessionMiddleware, secret_key="CHANGE_THIS_SECRET_KEY_IN_PRODUCTION_32chars")

# Static files & templates
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth.router)
app.include_router(users.router)


def init_db():
    """Create tables and seed admin account."""
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            hashed = pwd_context.hash("admin1234")
            admin_user = User(
                username="admin",
                email="admin@app.local",
                hashed_password=hashed,
                is_admin=True,
            )
            db.add(admin_user)
            db.commit()
            print("✅ Compte admin créé — username: admin | password: admin1234")
        else:
            print("ℹ️  Compte admin déjà existant.")
    finally:
        db.close()


@app.on_event("startup")
async def startup_event():
    init_db()


@app.get("/")
async def root():
    return RedirectResponse(url="/login", status_code=302)
