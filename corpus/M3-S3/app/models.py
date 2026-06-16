import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    shipping_address = Column(String, nullable=True)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    image_url = Column(String)
    category = Column(String)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_price = Column(Float)
    status = Column(String, default="En cours")
    created_at = Column(DateTime, default=datetime.utcnow)
    shipping_address = Column(String)
    card_number = Column(String)
    
    user = relationship("User")
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    price = Column(Float)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Injection du compte Admin obligatoire
    if not db.query(User).filter_by(email="admin@shop.com").first():
        admin = User(email="admin@shop.com", password="adminpassword", is_admin=True, shipping_address="Bureau Administration")
        db.add(admin)
        
    # Injection d'un compte Client d'exemple
    if not db.query(User).filter_by(email="client@shop.com").first():
        client = User(email="client@shop.com", password="clientpassword", is_admin=False, shipping_address="123 Rue de la République, Paris")
        db.add(client)
        
    # Injection des 5 produits d'exemple au démarrage
    if db.query(Product).count() == 0:
        products = [
            Product(name="Cafetière Expresso", description="Machine haute pression pour un café riche en arômes.", price=89.99, stock=10, image_url="https://images.unsplash.com/photo-1517668808822-9ebb02f2a0e5?w=500", category="Cuisine"),
            Product(name="Clavier Mécanique RGB", description="Switches bleus réactifs avec rétroéclairage personnalisable.", price=59.99, stock=15, image_url="https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=500", category="Informatique"),
            Product(name="Souris Gaming Sans Fil", description="Capteur optique 16 000 DPI ultra-précis.", price=39.99, stock=25, image_url="https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=500", category="Informatique"),
            Product(name="Sac à Dos Urbain", description="Sac étanche et ergonomique avec compartiment PC 15 pouces.", price=45.00, stock=8, image_url="https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500", category="Mode"),
            Product(name="Montre Connectée Sport", description="Suivi cardiaque en direct et notifications intelligentes.", price=129.99, stock=5, image_url="https://images.unsplash.com/photo-1542496658-e33a6d0d50f6?w=500", category="Électronique"),
        ]
        db.bulk_save_objects(products)
    db.commit()
    db.close()