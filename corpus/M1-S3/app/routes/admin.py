from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from models import get_db, Product, Category, Order
from routes.auth import require_admin

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="templates")

def admin_or_redirect(request, db):
    return require_admin(request, db)

@router.get("")
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = admin_or_redirect(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    products = db.query(Product).order_by(Product.id.desc()).all()
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "user": user, "products": products, "orders": orders})

@router.get("/products/new")
def new_product_page(request: Request, db: Session = Depends(get_db)):
    user = admin_or_redirect(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse("product_form.html", {"request": request, "user": user, "product": None, "categories": db.query(Category).all(), "action": "/admin/products/new"})

@router.post("/products/new")
def create_product(request: Request, name: str = Form(...), description: str = Form(...), price: float = Form(...), stock: int = Form(...), image_url: str = Form(...), category_name: str = Form(...), db: Session = Depends(get_db)):
    user = admin_or_redirect(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    category = db.query(Category).filter(Category.name == category_name).first() or Category(name=category_name)
    db.add(category); db.flush()
    db.add(Product(name=name, description=description, price=price, stock=stock, image_url=image_url, category_id=category.id))
    db.commit()
    return RedirectResponse("/admin", status_code=303)

@router.get("/products/{product_id}/edit")
def edit_product_page(product_id: int, request: Request, db: Session = Depends(get_db)):
    user = admin_or_redirect(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return RedirectResponse("/admin", status_code=303)
    return templates.TemplateResponse("product_form.html", {"request": request, "user": user, "product": product, "categories": db.query(Category).all(), "action": f"/admin/products/{product.id}/edit"})

@router.post("/products/{product_id}/edit")
def update_product(product_id: int, request: Request, name: str = Form(...), description: str = Form(...), price: float = Form(...), stock: int = Form(...), image_url: str = Form(...), category_name: str = Form(...), db: Session = Depends(get_db)):
    user = admin_or_redirect(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        category = db.query(Category).filter(Category.name == category_name).first() or Category(name=category_name)
        db.add(category); db.flush()
        product.name = name; product.description = description; product.price = price; product.stock = stock; product.image_url = image_url; product.category_id = category.id
        db.commit()
    return RedirectResponse("/admin", status_code=303)

@router.post("/products/{product_id}/delete")
def delete_product(product_id: int, request: Request, db: Session = Depends(get_db)):
    user = admin_or_redirect(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        db.delete(product); db.commit()
    return RedirectResponse("/admin", status_code=303)

@router.post("/orders/{order_id}/status")
def update_order_status(order_id: int, request: Request, status: str = Form(...), db: Session = Depends(get_db)):
    user = admin_or_redirect(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    if status not in ["en cours", "expédiée", "livrée"]:
        status = "en cours"
    order = db.query(Order).filter(Order.id == order_id).first()
    if order:
        order.status = status; db.commit()
    return RedirectResponse("/admin", status_code=303)
