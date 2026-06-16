from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, LeaveRequest, RoleEnum, LeaveStatusEnum
from passlib.context import CryptContext
from datetime import date, timedelta
import os

DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return

        # Admin
        admin = User(
            email="admin@company.com",
            full_name="Alice Dupont",
            hashed_password=pwd_context.hash("admin123"),
            role=RoleEnum.admin,
            department="Direction",
            salary=8500.0,
            position="DRH",
            phone="0601010101",
            hire_date=date(2018, 1, 15),
        )
        db.add(admin)
        db.flush()

        # Managers
        mgr1 = User(
            email="manager1@company.com",
            full_name="Bob Martin",
            hashed_password=pwd_context.hash("manager123"),
            role=RoleEnum.manager,
            department="Développement",
            salary=5800.0,
            position="Lead Dev",
            phone="0602020202",
            hire_date=date(2019, 3, 10),
            manager_id=admin.id,
        )
        mgr2 = User(
            email="manager2@company.com",
            full_name="Claire Bernard",
            hashed_password=pwd_context.hash("manager123"),
            role=RoleEnum.manager,
            department="Marketing",
            salary=5500.0,
            position="Directrice Marketing",
            phone="0603030303",
            hire_date=date(2020, 6, 1),
            manager_id=admin.id,
        )
        db.add_all([mgr1, mgr2])
        db.flush()

        # Employees - Développement
        emp1 = User(
            email="emp1@company.com",
            full_name="David Lefebvre",
            hashed_password=pwd_context.hash("emp123"),
            role=RoleEnum.employee,
            department="Développement",
            salary=3800.0,
            position="Développeur Backend",
            phone="0604040404",
            hire_date=date(2021, 9, 1),
            manager_id=mgr1.id,
        )
        emp2 = User(
            email="emp2@company.com",
            full_name="Emma Rousseau",
            hashed_password=pwd_context.hash("emp123"),
            role=RoleEnum.employee,
            department="Développement",
            salary=3600.0,
            position="Développeuse Frontend",
            phone="0605050505",
            hire_date=date(2022, 2, 14),
            manager_id=mgr1.id,
        )
        emp3 = User(
            email="emp3@company.com",
            full_name="François Petit",
            hashed_password=pwd_context.hash("emp123"),
            role=RoleEnum.employee,
            department="Développement",
            salary=3400.0,
            position="Développeur Fullstack",
            phone="0606060606",
            hire_date=date(2023, 1, 3),
            manager_id=mgr1.id,
        )
        # Employees - Marketing
        emp4 = User(
            email="emp4@company.com",
            full_name="Gabrielle Simon",
            hashed_password=pwd_context.hash("emp123"),
            role=RoleEnum.employee,
            department="Marketing",
            salary=3200.0,
            position="Chargée de communication",
            phone="0607070707",
            hire_date=date(2021, 5, 20),
            manager_id=mgr2.id,
        )
        emp5 = User(
            email="emp5@company.com",
            full_name="Hugo Lambert",
            hashed_password=pwd_context.hash("emp123"),
            role=RoleEnum.employee,
            department="Marketing",
            salary=3100.0,
            position="Community Manager",
            phone="0608080808",
            hire_date=date(2022, 11, 7),
            manager_id=mgr2.id,
        )
        db.add_all([emp1, emp2, emp3, emp4, emp5])
        db.flush()

        # Sample leave requests
        today = date.today()
        leaves = [
            LeaveRequest(user_id=emp1.id, manager_id=mgr1.id,
                         start_date=today + timedelta(days=5), end_date=today + timedelta(days=10),
                         reason="Vacances été", status=LeaveStatusEnum.pending),
            LeaveRequest(user_id=emp2.id, manager_id=mgr1.id,
                         start_date=today - timedelta(days=20), end_date=today - timedelta(days=15),
                         reason="Congé familial", status=LeaveStatusEnum.approved,
                         manager_comment="Accordé sans problème"),
            LeaveRequest(user_id=emp3.id, manager_id=mgr1.id,
                         start_date=today + timedelta(days=2), end_date=today + timedelta(days=4),
                         reason="Rendez-vous médical", status=LeaveStatusEnum.refused,
                         manager_comment="Période chargée, reporter si possible"),
            LeaveRequest(user_id=emp4.id, manager_id=mgr2.id,
                         start_date=today + timedelta(days=14), end_date=today + timedelta(days=21),
                         reason="Congés annuels", status=LeaveStatusEnum.pending),
            LeaveRequest(user_id=emp5.id, manager_id=mgr2.id,
                         start_date=today - timedelta(days=5), end_date=today - timedelta(days=2),
                         reason="Mariage", status=LeaveStatusEnum.approved,
                         manager_comment="Félicitations !"),
        ]
        db.add_all(leaves)
        db.commit()
        print("✅ Base de données initialisée avec les données d'exemple.")
    except Exception as e:
        db.rollback()
        print(f"Erreur init DB: {e}")
    finally:
        db.close()
