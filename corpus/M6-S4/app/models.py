from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Date,
    Enum,
    ForeignKey,
    Float,
    create_engine,
    func,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

ROLE_EMPLOYEE = "employee"
ROLE_MANAGER = "manager"
ROLE_ADMIN = "admin"

LEAVE_PENDING = "pending"
LEAVE_APPROVED = "approved"
LEAVE_REJECTED = "rejected"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default=ROLE_EMPLOYEE)
    department = Column(String, nullable=True)
    salary = Column(Float, nullable=False, default=0.0)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    photo_filename = Column(String, nullable=True)

    manager = relationship("User", remote_side=[id], backref="team_members")

    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN

    def is_manager(self) -> bool:
        return self.role == ROLE_MANAGER

    def is_employee(self) -> bool:
        return self.role == ROLE_EMPLOYEE


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(String, nullable=True)
    status = Column(String, nullable=False, default=LEAVE_PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("User", foreign_keys=[employee_id])
    manager = relationship("User", foreign_keys=[manager_id])


DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)
    from sqlalchemy.orm import Session
    from hashlib import sha256

    db: Session = SessionLocal()

    def hash_password(p: str) -> str:
        return sha256(p.encode("utf-8")).hexdigest()

    # S'il y a déjà des utilisateurs, on ne réinjecte pas
    if db.query(User).count() > 0:
        db.close()
        return

    # Admin
    admin = User(
        full_name="Admin User",
        email="admin@example.com",
        password_hash=hash_password("admin123"),
        role=ROLE_ADMIN,
        department="Direction",
        salary=80000,
    )
    db.add(admin)
    db.flush()

    # Managers
    manager1 = User(
        full_name="Manager One",
        email="manager1@example.com",
        password_hash=hash_password("manager123"),
        role=ROLE_MANAGER,
        department="IT",
        salary=60000,
        manager_id=admin.id,
    )
    manager2 = User(
        full_name="Manager Two",
        email="manager2@example.com",
        password_hash=hash_password("manager123"),
        role=ROLE_MANAGER,
        department="HR",
        salary=58000,
        manager_id=admin.id,
    )
    db.add_all([manager1, manager2])
    db.flush()

    # Employés (5, répartis sur 2 départements)
    employees = [
        User(
            full_name="Employee One",
            email="emp1@example.com",
            password_hash=hash_password("emp123"),
            role=ROLE_EMPLOYEE,
            department="IT",
            salary=40000,
            manager_id=manager1.id,
        ),
        User(
            full_name="Employee Two",
            email="emp2@example.com",
            password_hash=hash_password("emp123"),
            role=ROLE_EMPLOYEE,
            department="IT",
            salary=42000,
            manager_id=manager1.id,
        ),
        User(
            full_name="Employee Three",
            email="emp3@example.com",
            password_hash=hash_password("emp123"),
            role=ROLE_EMPLOYEE,
            department="HR",
            salary=38000,
            manager_id=manager2.id,
        ),
        User(
            full_name="Employee Four",
            email="emp4@example.com",
            password_hash=hash_password("emp123"),
            role=ROLE_EMPLOYEE,
            department="HR",
            salary=39000,
            manager_id=manager2.id,
        ),
        User(
            full_name="Employee Five",
            email="emp5@example.com",
            password_hash=hash_password("emp123"),
            role=ROLE_EMPLOYEE,
            department="IT",
            salary=41000,
            manager_id=manager1.id,
        ),
    ]
    db.add_all(employees)
    db.commit()
    db.close()
