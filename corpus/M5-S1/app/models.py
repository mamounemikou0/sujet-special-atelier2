from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from passlib.context import CryptContext

SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)
    
    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.hashed_password)

def init_db():
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Créer le compte admin par défaut
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=User.hash_password("admin123"),
                is_admin=True
            )
            db.add(admin_user)
            db.commit()
            print("Compte admin créé avec succès!")
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()