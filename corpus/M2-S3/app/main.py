from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from database import engine, SessionLocal
import models
import auth
import os

from routes.auth_routes import router as auth_router
from routes.product_routes import router as product_router
from routes.cart_routes import router as cart_router
from routes.order_routes import router as order_router


def seed_database():
    db = SessionLocal()
    try:
        # Create admin
        admin = db.query(models.User).filter(models.User.email == "admin@shop.com").first()
        if not admin:
            admin = models.User(
                email="admin@shop.com",
                hashed_password=auth.hash_password("admin123"),
                full_name="Admin",
                is_admin=True,
            )
            db.add(admin)

        # Create categories
        cats = {}
        for name, slug in [
            ("Électronique", "electronique"),
            ("Vêtements", "vetements"),
            ("Maison", "maison"),
            ("Sport", "sport"),
        ]:
            cat = db.query(models.Category).filter(models.Category.slug == slug).first()
            if not cat:
                cat = models.Category(name=name, slug=slug)
                db.add(cat)
                db.flush()
            cats[slug] = cat

        # Sample products
        sample_products = [
            {
                "name": "Casque Audio Pro",
                "description": "Casque sans fil avec réduction de bruit active, autonomie 30h, son haute fidélité.",
                "price": 149.99,
                "stock": 25,
                "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&q=80",
                "category_slug": "electronique",
            },
            {
                "name": "T-Shirt Premium Coton",
                "description": "T-shirt 100% coton bio, coupe classique, disponible en plusieurs coloris.",
                "price": 34.99,
                "stock": 100,
                "image_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600&q=80",
                "category_slug": "vetements",
            },
            {
                "name": "Lampe de Bureau LED",
                "description": "Lampe LED réglable en température et intensité, bras articulé, port USB intégré.",
                "price": 59.99,
                "stock": 40,
                "image_url": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=600&q=80",
                "category_slug": "maison",
            },
            {
                "name": "Tapis de Yoga Premium",
                "description": "Tapis antidérapant 6mm épaisseur, matière écologique, sangle de transport incluse.",
                "price": 44.99,
                "stock": 60,
                "image_url": "https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?w=600&q=80",
                "category_slug": "sport",
            },
            {
                "name": "Montre Connectée Sport",
                "description": "Suivi activité, GPS intégré, étanche 50m, autonomie 7 jours, compatible iOS & Android.",
                "price": 199.99,
                "stock": 15,
                "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&q=80",
                "category_slug": "electronique",
            },
        ]

        for p_data in sample_products:
            exists = db.query(models.Product).filter(models.Product.name == p_data["name"]).first()
            if not exists:
                cat = cats.get(p_data["category_slug"])
                product = models.Product(
                    name=p_data["name"],
                    description=p_data["description"],
                    price=p_data["price"],
                    stock=p_data["stock"],
                    image_url=p_data["image_url"],
                    category_id=cat.id if cat else None,
                )
                db.add(product)

        db.commit()
        print("✅ Database seeded — admin@shop.com / admin123")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    seed_database()
    yield


app = FastAPI(title="E-Boutique", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(product_router)
app.include_router(cart_router)
app.include_router(order_router)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    return FileResponse("templates/index.html")


@app.get("/")
async def root():
    return FileResponse("templates/index.html")
