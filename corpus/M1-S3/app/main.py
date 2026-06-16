from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from models import Base, engine, SessionLocal, User, Category, Product
from routes import shop, auth, admin

app = FastAPI(title="Petite e-boutique FastAPI")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(shop.router)
app.include_router(auth.router)
app.include_router(admin.router)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SAMPLE_PRODUCTS = [
    ("Carnet artisanal", "Carnet A5 avec couverture rigide, idéal pour notes et croquis.", 12.90, 20, "Papeterie", "https://images.unsplash.com/photo-1517842645767-c639042777db?auto=format&fit=crop&w=900&q=80"),
    ("Bougie vanille", "Bougie parfumée coulée à la main, environ 35 heures de combustion.", 16.50, 15, "Maison", "https://images.unsplash.com/photo-1602874801006-66cf1d2db372?auto=format&fit=crop&w=900&q=80"),
    ("Tote bag coton", "Sac réutilisable en coton épais avec poche intérieure.", 14.00, 30, "Accessoires", "https://images.unsplash.com/photo-1590874103328-eac38a683ce7?auto=format&fit=crop&w=900&q=80"),
    ("Mug céramique", "Mug blanc 330 ml, compatible lave-vaisselle et micro-ondes.", 10.90, 25, "Maison", "https://images.unsplash.com/photo-1517256064527-09c73fc73e38?auto=format&fit=crop&w=900&q=80"),
    ("Affiche minimaliste", "Affiche décorative 30x40 cm imprimée sur papier mat premium.", 18.00, 12, "Décoration", "https://images.unsplash.com/photo-1513519245088-0e12902e5a38?auto=format&fit=crop&w=900&q=80"),
]

def seed_data():
    db: Session = SessionLocal()
    try:
        if not db.query(User).filter(User.email == "admin@example.com").first():
            db.add(User(
                email="admin@example.com",
                full_name="Administrateur",
                password_hash=pwd_context.hash("admin1234"),
                shipping_address="Adresse admin",
                role="admin",
            ))
        for _, _, _, _, category_name, _ in SAMPLE_PRODUCTS:
            if not db.query(Category).filter(Category.name == category_name).first():
                db.add(Category(name=category_name))
        db.commit()
        if db.query(Product).count() == 0:
            for name, desc, price, stock, category_name, image_url in SAMPLE_PRODUCTS:
                category = db.query(Category).filter(Category.name == category_name).first()
                db.add(Product(name=name, description=desc, price=price, stock=stock, category_id=category.id, image_url=image_url))
            db.commit()
    finally:
        db.close()

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    seed_data()
