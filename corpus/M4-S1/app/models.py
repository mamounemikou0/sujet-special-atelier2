from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
import os

# Configuration SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Contexte pour le hachage des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Modèle Utilisateur
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)

# Création des tables
Base.metadata.create_all(bind=engine)

# Initialisation de la base (création du compte admin si inexistant)
def init_db():
    db = SessionLocal()
    admin_exists = db.query(User).filter(User.email == "admin@example.com").first()
    if not admin_exists:
        admin = User(
            username="admin",
            email="admin@example.com",
            hashed_password=pwd_context.hash("admin123"),
            is_admin=True
        )
        db.add(admin)
        db.commit()
    db.close()

# Appel à l'initialisation
init_db()