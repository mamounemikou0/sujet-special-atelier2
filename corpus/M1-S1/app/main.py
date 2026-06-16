from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from models import Base, engine, SessionLocal, User
from routes.auth import router as auth_router
from routes.users import router as users_router
from routes.admin import router as admin_router
from passlib.context import CryptContext

app = FastAPI()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

Base.metadata.create_all(bind=engine)

db = SessionLocal()

admin_exists = db.query(User).filter(User.username == "admin").first()

if not admin_exists:
    admin_user = User(
        email="admin@example.com",
        username="admin",
        password=pwd_context.hash("admin123"),
        is_admin=True
    )
    db.add(admin_user)
    db.commit()

db.close()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(admin_router)