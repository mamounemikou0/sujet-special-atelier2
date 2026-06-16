from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    Boolean,
    ForeignKey,
    Enum,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session
import enum
import hashlib
import os

DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class OrderStatus(str, enum.Enum):
    pending = "en cours"
    shipped = "expédiée"
    delivered = "livrée"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    address = Column(Text, nullable=True)

    orders = relationship("Order", back_populates="user")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    image_url = Column(String(500), nullable=True)
    category = Column(String(100), nullable=True)

    items = relationship("OrderItem", back_populates="product")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.pending)
    total_amount = Column(Float, nullable=False, default=0.0)
    shipping_address = Column(Text, nullable=False)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="items")


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def create_db_and_seed():
    if not os.path.exists("app.db"):
        Base.metadata.create_all(bind=engine)
    else:
        Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Admin user
        admin_email = "admin@example.com"
        admin = db.query(User).filter(User.email == admin_email).first()
        if not admin:
            admin = User(
                email=admin_email,
                password_hash=hash_password("admin123"),
                is_admin=True,
                address="Adresse admin",
            )
            db.add(admin)

        # Sample products
        if db.query(Product).count() == 0:
            products = [
                Product(
                    name="T-shirt blanc",
                    description="T-shirt en coton blanc, confortable.",
                    price=19.99,
                    stock=20,
                    image_url="https://via.placeholder.com/200x200?text=T-shirt+blanc",
                    category="Vêtements",
                ),
                Product(
                    name="Mug en céramique",
                    description="Mug pour café ou thé, 300ml.",
                    price=9.99,
                    stock=50,
                    image_url="https://via.placeholder.com/200x200?text=Mug",
                    category="Maison",
                ),
                Product(
                    name="Casquette noire",
                    description="Casquette noire unisexe.",
                    price=14.99,
                    stock=15,
                    image_url="https://via.placeholder.com/200x200?text=Casquette",
                    category="Accessoires",
                ),
                Product(
                    name="Sac à dos",
                    description="Sac à dos pratique pour le quotidien.",
                    price=39.99,
                    stock=10,
                    image_url="https://via.placeholder.com/200x200?text=Sac+à+dos",
                    category="Bagagerie",
                ),
                Product(
                    name="Carnet de notes",
                    description="Carnet A5, 100 pages lignées.",
                    price=4.99,
                    stock=100,
                    image_url="https://via.placeholder.com/200x200?text=Carnet",
                    category="Papeterie",
                ),
            ]
            db.add_all(products)

        db.commit()
    finally:
        db.close()
