from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_
from models import get_db, Product, Category, Order, OrderItem
from routes.auth import get_current_user, require_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_cart(request: Request):
    raw = request.cookies.get("cart", "")
    cart = {}
    for part in raw.split("|"):
        if ":" in part:
            pid, qty = part.split(":", 1)
            if pid.isdigit() and qty.isdigit() and int(qty) > 0:
                cart[int(pid)] = int(qty)
    return cart

def cart_cookie(cart):
    return "|".join(f"{pid}:{qty}" for pid, qty in cart.items() if qty > 0)

def cart_details(db: Session, cart):
    items, total = [], 0.0
    for pid, qty in cart.items():
        product = db.query(Product).filter(Product.id == pid).first()
        if product:
            qty = min(qty, product.stock)
            subtotal = product.price * qty
            total += subtotal
            items.append({"product": product, "quantity": qty, "subtotal": subtotal})
    return items, total

@router.get("/")
def home(request: Request, q: str = "", category: str = "", db: Session = Depends(get_db)):
    query = db.query(Product)
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))
    if category:
        query = query.join(Category).filter(Category.name == category)
    products = query.order_by(Product.id.desc()).all()
    categories = db.query(Category).order_by(Category.name).all()
    return templates.TemplateResponse("index.html", {"request": request, "products": products, "categories": categories, "q": q, "selected_category": category, "user": get_current_user(request, db)})

@router.post("/cart/add/{product_id}")
def add_to_cart(product_id: int, request: Request, quantity: int = Form(1), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return RedirectResponse("/", status_code=303)
    cart = get_cart(request)
    cart[product_id] = min(product.stock, cart.get(product_id, 0) + max(1, quantity))
    response = RedirectResponse("/cart", status_code=303)
    response.set_cookie("cart", cart_cookie(cart), samesite="lax")
    return response

@router.get("/cart")
def cart_page(request: Request, db: Session = Depends(get_db)):
    items, total = cart_details(db, get_cart(request))
    return templates.TemplateResponse("cart.html", {"request": request, "items": items, "total": total, "user": get_current_user(request, db)})

@router.post("/cart/update/{product_id}")
def update_cart(product_id: int, request: Request, quantity: int = Form(...)):
    cart = get_cart(request)
    if quantity <= 0:
        cart.pop(product_id, None)
    else:
        cart[product_id] = quantity
    response = RedirectResponse("/cart", status_code=303)
    response.set_cookie("cart", cart_cookie(cart), samesite="lax")
    return response

@router.post("/cart/remove/{product_id}")
def remove_cart(product_id: int, request: Request):
    cart = get_cart(request)
    cart.pop(product_id, None)
    response = RedirectResponse("/cart", status_code=303)
    response.set_cookie("cart", cart_cookie(cart), samesite="lax")
    return response

@router.get("/checkout")
def checkout_page(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    items, total = cart_details(db, get_cart(request))
    return templates.TemplateResponse("checkout.html", {"request": request, "items": items, "total": total, "user": user, "error": None})

@router.post("/checkout")
def checkout(request: Request, card_number: str = Form(...), db: Session = Depends(get_db)):
    user = require_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    cart = get_cart(request)
    items, total = cart_details(db, cart)
    clean_card = card_number.replace(" ", "")
    if not clean_card.isdigit() or len(clean_card) != 16:
        return templates.TemplateResponse("checkout.html", {"request": request, "items": items, "total": total, "user": user, "error": "Le faux numéro de carte doit contenir exactement 16 chiffres."})
    if not items:
        return RedirectResponse("/cart", status_code=303)
    for item in items:
        if item["quantity"] > item["product"].stock:
            return templates.TemplateResponse("checkout.html", {"request": request, "items": items, "total": total, "user": user, "error": "Stock insuffisant pour un produit."})
    order = Order(user_id=user.id, total=total, shipping_address=user.shipping_address, status="en cours")
    db.add(order); db.flush()
    for item in items:
        product = item["product"]
        product.stock -= item["quantity"]
        db.add(OrderItem(order_id=order.id, product_id=product.id, product_name=product.name, unit_price=product.price, quantity=item["quantity"]))
    db.commit()
    response = RedirectResponse(f"/orders/{order.id}", status_code=303)
    response.delete_cookie("cart")
    return response

@router.get("/orders")
def orders(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    orders = db.query(Order).filter(Order.user_id == user.id).order_by(Order.created_at.desc()).all()
    return templates.TemplateResponse("orders.html", {"request": request, "orders": orders, "user": user})

@router.get("/orders/{order_id}")
def order_detail(order_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        return RedirectResponse("/orders", status_code=303)
    return templates.TemplateResponse("order_detail.html", {"request": request, "order": order, "user": user})
