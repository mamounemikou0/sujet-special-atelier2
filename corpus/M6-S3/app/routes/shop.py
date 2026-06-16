from typing import Optional

from fastapi import APIRouter, Depends, Form, Request, Cookie
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from models import Product, Order, OrderItem, get_db
from deps import get_current_user, require_user
from session_store import CARTS

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
def home(
    request: Request,
    q: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    query = db.query(Product)
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))
    if category:
        query = query.filter(Product.category == category)
    products = query.all()
    categories = (
        db.query(Product.category)
        .distinct()
        .filter(Product.category.isnot(None))
        .all()
    )
    categories = [c[0] for c in categories]
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "products": products,
            "categories": categories,
            "selected_category": category,
            "search": q or "",
            "user": user,
        },
    )


@router.get("/product/{product_id}")
def product_detail(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(
        "product_detail.html",
        {"request": request, "product": product, "user": user},
    )


@router.post("/cart/add/{product_id}")
def add_to_cart(
    product_id: int,
    quantity: int = Form(1),
    session_id: Optional[str] = Cookie(default=None),
):
    if not session_id:
        # panier invité : on crée un faux id de session côté client
        resp = RedirectResponse(url="/", status_code=302)
        return resp
    cart = CARTS.setdefault(session_id, {})
    cart[product_id] = cart.get(product_id, 0) + max(quantity, 1)
    return RedirectResponse(url="/cart", status_code=302)


@router.get("/cart")
def view_cart(
    request: Request,
    db: Session = Depends(get_db),
    session_id: Optional[str] = Cookie(default=None),
    user=Depends(get_current_user),
):
    cart_items = []
    total = 0.0
    if session_id and session_id in CARTS:
        cart = CARTS[session_id]
        for pid, qty in cart.items():
            product = db.query(Product).filter(Product.id == pid).first()
            if product:
                line_total = product.price * qty
                total += line_total
                cart_items.append(
                    {"product": product, "quantity": qty, "line_total": line_total}
                )
    return templates.TemplateResponse(
        "cart.html",
        {
            "request": request,
            "cart_items": cart_items,
            "total": total,
            "user": user,
        },
    )


@router.post("/cart/update/{product_id}")
def update_cart_item(
    product_id: int,
    quantity: int = Form(...),
    session_id: Optional[str] = Cookie(default=None),
):
    if session_id and session_id in CARTS:
        cart = CARTS[session_id]
        if quantity <= 0:
            cart.pop(product_id, None)
        else:
            cart[product_id] = quantity
    return RedirectResponse(url="/cart", status_code=302)


@router.post("/cart/remove/{product_id}")
def remove_cart_item(
    product_id: int,
    session_id: Optional[str] = Cookie(default=None),
):
    if session_id and session_id in CARTS:
        cart = CARTS[session_id]
        cart.pop(product_id, None)
    return RedirectResponse(url="/cart", status_code=302)


@router.get("/checkout")
def checkout_page(
    request: Request,
    db: Session = Depends(get_db),
    session_id: Optional[str] = Cookie(default=None),
    user=Depends(require_user),
):
    cart_items = []
    total = 0.0
    if not session_id or session_id not in CARTS or not CARTS[session_id]:
        return RedirectResponse(url="/cart", status_code=302)
    cart = CARTS[session_id]
    for pid, qty in cart.items():
        product = db.query(Product).filter(Product.id == pid).first()
        if product:
            line_total = product.price * qty
            total += line_total
            cart_items.append(
                {"product": product, "quantity": qty, "line_total": line_total}
            )
    return templates.TemplateResponse(
        "checkout.html",
        {
            "request": request,
            "cart_items": cart_items,
            "total": total,
            "user": user,
        },
    )


@router.post("/checkout")
def checkout(
    request: Request,
    credit_card: str = Form(...),
    address: str = Form(...),
    db: Session = Depends(get_db),
    session_id: Optional[str] = Cookie(default=None),
    user=Depends(require_user),
):
    if not session_id or session_id not in CARTS or not CARTS[session_id]:
        return RedirectResponse(url="/cart", status_code=302)

    if not (credit_card.isdigit() and len(credit_card) == 16):
        return templates.TemplateResponse(
            "checkout.html",
            {
                "request": request,
                "error": "Numéro de carte invalide (16 chiffres requis)",
                "user": user,
                "cart_items": [],
                "total": 0.0,
            },
            status_code=400,
        )

    cart = CARTS[session_id]
    total = 0.0
    items_data = []
    for pid, qty in cart.items():
        product = db.query(Product).filter(Product.id == pid).first()
        if not product or product.stock < qty:
            return templates.TemplateResponse(
                "checkout.html",
                {
                    "request": request,
                    "error": f"Stock insuffisant pour le produit ID {pid}",
                    "user": user,
                    "cart_items": [],
                    "total": 0.0,
                },
                status_code=400,
            )
        line_total = product.price * qty
        total += line_total
        items_data.append((product, qty))

    order = Order(
        user_id=user.id,
        status="en cours",
        total_amount=total,
        shipping_address=address or user.address or "",
    )
    db.add(order)
    db.flush()

    for product, qty in items_data:
        item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=qty,
            unit_price=product.price,
        )
        product.stock -= qty
        db.add(item)

    db.commit()
    CARTS[session_id] = {}

    return RedirectResponse(url="/orders", status_code=302)


@router.get("/orders")
def my_orders(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    orders = (
        db.query(Order)
        .filter(Order.user_id == user.id)
        .order_by(Order.id.desc())
        .all()
    )
    return templates.TemplateResponse(
        "orders.html",
        {"request": request, "orders": orders, "user": user},
    )
