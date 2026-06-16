from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import Optional
import re

from models import SessionLocal, User, Product, Cart, Order, OrderItem, engine, Base

app = FastAPI(title="E-Boutique")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database with sample data
def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Check if admin exists
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            email="admin@eboutique.com",
            username="admin",
            is_admin=True
        )
        admin.set_password("admin123")
        db.add(admin)
    
    # Check if products exist
    if db.query(Product).count() == 0:
        products = [
            Product(
                name="Smartphone XYZ",
                description="Smartphone dernier cri avec écran OLED 6.5 pouces",
                price=599.99,
                stock=10,
                image_url="https://picsum.photos/id/0/200/200",
                category="Électronique"
            ),
            Product(
                name="Casque Audio Pro",
                description="Casque audio sans fil avec réduction de bruit",
                price=149.99,
                stock=15,
                image_url="https://picsum.photos/id/1/200/200",
                category="Audio"
            ),
            Product(
                name="Sac à Dos Urbain",
                description="Sac à dos résistant à l'eau, 20L",
                price=49.99,
                stock=20,
                image_url="https://picsum.photos/id/2/200/200",
                category="Accessoires"
            ),
            Product(
                name="Montre Connectée",
                description="Montre intelligente avec suivi d'activité",
                price=249.99,
                stock=8,
                image_url="https://picsum.photos/id/3/200/200",
                category="Électronique"
            ),
            Product(
                name="Livre Python pour Débutants",
                description="Apprenez Python pas à pas",
                price=39.99,
                stock=25,
                image_url="https://picsum.photos/id/4/200/200",
                category="Livres"
            )
        ]
        for product in products:
            db.add(product)
    
    db.commit()
    db.close()

@app.on_event("startup")
def startup_event():
    init_db()

# Helper functions
def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    if user_id:
        user = db.query(User).filter(User.id == int(user_id)).first()
        return user
    return None

def is_admin(user):
    return user and user.is_admin

# ============ ROUTES ============

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, search: Optional[str] = None, category: Optional[str] = None, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    query = db.query(Product)
    
    if search:
        query = query.filter(Product.name.contains(search))
    if category and category != "all":
        query = query.filter(Product.category == category)
    
    products = query.all()
    categories = db.query(Product.category).distinct().all()
    
    # Get cart count
    cart_count = 0
    if user:
        cart_count = db.query(Cart).filter(Cart.user_id == user.id).count()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "products": products,
        "categories": [c[0] for c in categories],
        "selected_category": category,
        "search": search,
        "user": user,
        "cart_count": cart_count
    })

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register(
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    address: str = Form(...),
    db: Session = Depends(get_db)
):
    # Check if user exists
    existing = db.query(User).filter(
        (User.email == email) | (User.username == username)
    ).first()
    
    if existing:
        return templates.TemplateResponse("register.html", {
            "request": {"method": "POST"},
            "error": "Email ou nom d'utilisateur déjà utilisé"
        })
    
    user = User(email=email, username=username, address=address)
    user.set_password(password)
    db.add(user)
    db.commit()
    
    response = RedirectResponse(url="/login", status_code=303)
    return response

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    
    if not user or not user.check_password(password):
        return templates.TemplateResponse("login.html", {
            "request": {"method": "POST"},
            "error": "Identifiants invalides"
        })
    
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="user_id", value=str(user.id))
    return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("user_id")
    return response

@app.post("/cart/add")
async def add_to_cart(
    request: Request,
    product_id: int = Form(...),
    quantity: int = Form(1),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product or product.stock < quantity:
        return RedirectResponse(url="/", status_code=303)
    
    cart_item = db.query(Cart).filter(
        Cart.user_id == user.id,
        Cart.product_id == product_id
    ).first()
    
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = Cart(user_id=user.id, product_id=product_id, quantity=quantity)
        db.add(cart_item)
    
    db.commit()
    return RedirectResponse(url="/cart", status_code=303)

@app.get("/cart", response_class=HTMLResponse)
async def view_cart(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    cart_items = db.query(Cart).filter(Cart.user_id == user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    return templates.TemplateResponse("cart.html", {
        "request": request,
        "cart_items": cart_items,
        "total": total,
        "user": user,
        "cart_count": len(cart_items)
    })

@app.post("/cart/update")
async def update_cart(
    request: Request,
    cart_id: int = Form(...),
    quantity: int = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    cart_item = db.query(Cart).filter(Cart.id == cart_id, Cart.user_id == user.id).first()
    if cart_item:
        if quantity <= 0:
            db.delete(cart_item)
        else:
            cart_item.quantity = quantity
        db.commit()
    
    return RedirectResponse(url="/cart", status_code=303)

@app.get("/checkout", response_class=HTMLResponse)
async def checkout_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    cart_items = db.query(Cart).filter(Cart.user_id == user.id).all()
    if not cart_items:
        return RedirectResponse(url="/cart", status_code=303)
    
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    return templates.TemplateResponse("checkout.html", {
        "request": request,
        "cart_items": cart_items,
        "total": total,
        "user": user,
        "cart_count": len(cart_items)
    })

@app.post("/checkout")
async def process_checkout(
    request: Request,
    card_number: str = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Validate credit card number (16 digits)
    if not re.match(r'^\d{16}$', card_number):
        cart_items = db.query(Cart).filter(Cart.user_id == user.id).all()
        total = sum(item.product.price * item.quantity for item in cart_items)
        return templates.TemplateResponse("checkout.html", {
            "request": request,
            "cart_items": cart_items,
            "total": total,
            "user": user,
            "error": "Numéro de carte invalide (16 chiffres requis)"
        })
    
    cart_items = db.query(Cart).filter(Cart.user_id == user.id).all()
    if not cart_items:
        return RedirectResponse(url="/cart", status_code=303)
    
    # Create order
    total = sum(item.product.price * item.quantity for item in cart_items)
    order = Order(
        user_id=user.id,
        total_amount=total,
        shipping_address=user.address
    )
    db.add(order)
    db.flush()
    
    # Create order items and update stock
    for cart_item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=cart_item.product.id,
            product_name=cart_item.product.name,
            product_price=cart_item.product.price,
            quantity=cart_item.quantity
        )
        db.add(order_item)
        
        # Update stock
        cart_item.product.stock -= cart_item.quantity
        db.delete(cart_item)
    
    db.commit()
    
    return RedirectResponse(url="/orders", status_code=303)

@app.get("/orders", response_class=HTMLResponse)
async def orders_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    orders = db.query(Order).filter(Order.user_id == user.id).order_by(Order.order_date.desc()).all()
    
    return templates.TemplateResponse("orders.html", {
        "request": request,
        "orders": orders,
        "user": user
    })

# ============ ADMIN ROUTES ============

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not is_admin(user):
        return RedirectResponse(url="/", status_code=303)
    
    products = db.query(Product).all()
    orders = db.query(Order).order_by(Order.order_date.desc()).all()
    
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "products": products,
        "orders": orders,
        "user": user
    })

@app.post("/admin/product/add")
async def add_product(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),
    image_url: str = Form(...),
    category: str = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not is_admin(user):
        return RedirectResponse(url="/", status_code=303)
    
    product = Product(
        name=name,
        description=description,
        price=price,
        stock=stock,
        image_url=image_url,
        category=category
    )
    db.add(product)
    db.commit()
    
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/product/edit/{product_id}")
async def edit_product(
    product_id: int,
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),
    image_url: str = Form(...),
    category: str = Form(...),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        product.name = name
        product.description = description
        product.price = price
        product.stock = stock
        product.image_url = image_url
        product.category = category
        db.commit()
    
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/product/delete/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        db.delete(product)
        db.commit()
    
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/order/status/{order_id}")
async def update_order_status(
    order_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if order:
        order.status = status
        db.commit()
    
    return RedirectResponse(url="/admin", status_code=303)