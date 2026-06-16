from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from models import SessionLocal, Product, Order, OrderItem
import json
from urllib.parse import quote, unquote

router = APIRouter(prefix="/cart", tags=["Cart"])
templates = Jinja2Templates(directory="templates")

def get_cart_dict(request: Request) -> dict:
    cart_cookie = request.cookies.get("cart")
    if not cart_cookie:
        return {}
    try:
        return json.loads(unquote(cart_cookie))
    except Exception:
        return {}

@router.get("", response_class=HTMLResponse)
def view_cart(request: Request):
    db = SessionLocal()
    cart_dict = get_cart_dict(request)
    cart_items = []
    total = 0.0
    for p_id, qty in cart_dict.items():
        product = db.query(Product).filter(Product.id == int(p_id)).first()
        if product:
            item_total = product.price * qty
            total += item_total
            cart_items.append({"product": product, "quantity": qty, "total": item_total})
    db.close()
    return templates.TemplateResponse("cart.html", {"request": request, "cart_items": cart_items, "total": total})

@router.post("/add/{product_id}")
def add_to_cart(request: Request, product_id: int, quantity: int = Form(1)):
    cart_dict = get_cart_dict(request)
    p_id_str = str(product_id)
    cart_dict[p_id_str] = cart_dict.get(p_id_str, 0) + quantity
    response = RedirectResponse(url="/cart", status_code=303)
    response.set_cookie("cart", quote(json.dumps(cart_dict)))
    return response

@router.post("/update/{product_id}")
def update_cart(request: Request, product_id: int, quantity: int = Form(...)):
    cart_dict = get_cart_dict(request)
    p_id_str = str(product_id)
    if quantity <= 0:
        cart_dict.pop(p_id_str, None)
    else:
        cart_dict[p_id_str] = quantity
    response = RedirectResponse(url="/cart", status_code=303)
    response.set_cookie("cart", quote(json.dumps(cart_dict)))
    return response

@router.post("/remove/{product_id}")
def remove_from_cart(request: Request, product_id: int):
    cart_dict = get_cart_dict(request)
    cart_dict.pop(str(product_id), None)
    response = RedirectResponse(url="/cart", status_code=303)
    response.set_cookie("cart", quote(json.dumps(cart_dict)))
    return response

@router.get("/checkout", response_class=HTMLResponse)
def checkout_page(request: Request):
    user = request.state.user
    if not user:
        return RedirectResponse(url="/auth/login")
    db = SessionLocal()
    cart_dict = get_cart_dict(request)
    if not cart_dict:
        db.close()
        return RedirectResponse(url="/cart")
    cart_items = []
    total = 0.0
    for p_id, qty in cart_dict.items():
        product = db.query(Product).filter(Product.id == int(p_id)).first()
        if product:
            item_total = product.price * qty
            total += item_total
            cart_items.append({"product": product, "quantity": qty, "total": item_total})
    db.close()
    return templates.TemplateResponse("checkout.html", {"request": request, "cart_items": cart_items, "total": total})

@router.post("/checkout")
def process_checkout(request: Request, card_number: str = Form(...), shipping_address: str = Form(...)):
    user = request.state.user
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)
    
    clean_card = card_number.replace(" ", "").replace("-", "")
    if not clean_card.isdigit() or len(clean_card) != 16:
        return RedirectResponse(url="/cart/checkout?error=invalid_card", status_code=303)
        
    db = SessionLocal()
    cart_dict = get_cart_dict(request)
    if not cart_dict:
        db.close()
        return RedirectResponse(url="/catalog", status_code=303)
        
    total = 0.0
    order_items_to_create = []
    for p_id, qty in cart_dict.items():
        product = db.query(Product).filter(Product.id == int(p_id)).first()
        if product:
            if product.stock < qty:
                db.close()
                return RedirectResponse(url=f"/cart?error=stock_{product.id}", status_code=303)
            product.stock -= qty
            total += product.price * qty
            order_items_to_create.append(OrderItem(product_id=product.id, quantity=qty, price=product.price))
            
    masked_card = f"**** **** **** {clean_card[-4:]}"
    new_order = Order(user_id=user.id, total_price=total, status="En cours", shipping_address=shipping_address, card_number=masked_card)
    db.add(new_order)
    db.commit()
    
    for item in order_items_to_create:
        item.order_id = new_order.id
        db.add(item)
    db.commit()
    db.close()
    
    response = RedirectResponse(url="/catalog/orders", status_code=303)
    response.delete_cookie("cart")
    return response