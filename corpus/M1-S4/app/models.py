from datetime import date, datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

ROLE_EMPLOYEE = "Employé"
ROLE_MANAGER = "Manager"
ROLE_ADMIN = "Admin"
LEAVE_PENDING = "En attente"
LEAVE_APPROVED = "Approuvé"
LEAVE_REJECTED = "Refusé"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(80), nullable=False)
    last_name = Column(String(80), nullable=False)
    email = Column(String(160), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, default=ROLE_EMPLOYEE)
    department = Column(String(80), nullable=False)
    salary = Column(Float, nullable=False, default=0)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    profile_photo = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    manager = relationship("User", remote_side=[id], backref="team")
    leaves = relationship("LeaveRequest", back_populates="user", cascade="all, delete-orphan", foreign_keys="LeaveRequest.user_id")
    reviewed_leaves = relationship("LeaveRequest", foreign_keys="LeaveRequest.reviewed_by_id")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, default=LEAVE_PENDING)
    manager_comment = Column(Text, nullable=True)
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="leaves", foreign_keys=[user_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
