import hashlib
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False) # 'Admin', 'Manager', 'Employé'
    department = Column(String, nullable=False)
    salary = Column(Float, default=0.0)
    profile_pic = Column(String, default="default.png")
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    leaves = relationship("LeaveRequest", back_populates="user")

class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_date = Column(String, nullable=False)
    end_date = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    status = Column(String, default="En attente") # 'En attente', 'Approuvé', 'Refusé'

    user = relationship("User", back_populates="leaves")

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Injection automatique des données de démo si la table est vide
    if db.query(User).count() == 0:
        def get_hash(p: str): 
            return hashlib.sha256(p.encode()).hexdigest()
        
        # 1 Admin
        admin = User(email="admin@pme.com", hashed_password=get_hash("admin123"), name="Alice Admin", role="Admin", department="Direction", salary=6500.0)
        db.add(admin)
        db.commit()

        # 2 Managers
        m1 = User(email="m1@pme.com", hashed_password=get_hash("manager123"), name="Marc Tech", role="Manager", department="Tech", salary=4800.0)
        m2 = User(email="m2@pme.com", hashed_password=get_hash("manager123"), name="Mireille RH", role="Manager", department="Ressources Humaines", salary=4400.0)
        db.add_all([m1, m2])
        db.commit()

        # 5 Employés répartis dans les 2 départements
        emp1 = User(email="e1@pme.com", hashed_password=get_hash("emp123"), name="Thomas Dev", role="Employé", department="Tech", salary=3200.0, manager_id=m1.id)
        emp2 = User(email="e2@pme.com", hashed_password=get_hash("emp123"), name="Sarah Infra", role="Employé", department="Tech", salary=3500.0, manager_id=m1.id)
        emp3 = User(email="e3@pme.com", hashed_password=get_hash("emp123"), name="Kevin QA", role="Employé", department="Tech", salary=2900.0, manager_id=m1.id)
        emp4 = User(email="e4@pme.com", hashed_password=get_hash("emp123"), name="Hugo Paie", role="Employé", department="Ressources Humaines", salary=2800.0, manager_id=m2.id)
        emp5 = User(email="e5@pme.com", hashed_password=get_hash("emp123"), name="Emma Talent", role="Employé", department="Ressources Humaines", salary=3100.0, manager_id=m2.id)
        db.add_all([emp1, emp2, emp3, emp4, emp5])
        db.commit()
        
        # Exemple de demande de congé initiale
        req = LeaveRequest(user_id=emp1.id, start_date="2026-07-01", end_date="2026-07-15", reason="Vacances d'été", status="En attente")
        db.add(req)
        db.commit()
        
    db.close()