from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class Role(enum.Enum):
    EMPLOYEE = "Employé"
    MANAGER = "Manager"
    ADMIN = "Admin"

class Department(enum.Enum):
    IT = "IT"
    HR = "Ressources Humaines"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    role = Column(Enum(Role))
    department = Column(Enum(Department))
    salary = Column(Float, default=0.0)
    profile_picture = Column(String, default=None)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    manager = relationship("User", remote_side=[id], back_populates="team")
    team = relationship("User", back_populates="manager")
    leave_requests = relationship("LeaveRequest", back_populates="user")

class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    start_date = Column(Date)
    end_date = Column(Date)
    reason = Column(String)
    status = Column(String, default="En attente")  # En attente, Approuvé, Refusé
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="leave_requests")