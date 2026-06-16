from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class RoleEnum(str, enum.Enum):
    admin = "admin"
    manager = "manager"
    employee = "employee"


class LeaveStatusEnum(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    refused = "refused"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.employee)
    department = Column(String, nullable=True)
    salary = Column(Float, nullable=False, default=0.0)
    position = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    hire_date = Column(Date, nullable=True)
    profile_picture = Column(String, nullable=True, default=None)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    manager = relationship("User", remote_side=[id], backref="team_members")
    leave_requests = relationship("LeaveRequest", back_populates="user", foreign_keys="LeaveRequest.user_id")


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(Enum(LeaveStatusEnum), default=LeaveStatusEnum.pending)
    manager_comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="leave_requests", foreign_keys=[user_id])
    manager = relationship("User", foreign_keys=[manager_id])
