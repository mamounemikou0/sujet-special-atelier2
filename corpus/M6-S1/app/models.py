from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from passlib.hash import bcrypt

DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def verify_password(self, password: str) -> bool:
        return bcrypt.verify(password, self.password_hash)


def get_password_hash(password: str) -> str:
    return bcrypt.hash(password)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    # Create default admin if not exists
    db: Session = SessionLocal()
    try:
        admin = db.query(User).filter(User.is_admin == True).first()
        if not admin:
            admin_user = User(
                email="admin@example.com",
                username="admin",
                password_hash=get_password_hash("admin123"),
                is_admin=True,
            )
            db.add(admin_user)
            db.commit()
    finally:
        db.close()
