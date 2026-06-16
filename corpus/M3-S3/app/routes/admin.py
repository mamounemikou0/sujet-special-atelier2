from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from models import SessionLocal, Product, Order
from sqlalchemy.orm import Session

router = APIRouter(prefix="/admin", tags=["Admin"])
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    user = request.state.user
    if not user or not user.is_admin:
        return RedirectResponse(url="/catalog")
    products = db.query(Product).all()
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    return templates.TemplateResponse("admin.html", {"request": request, "products": products, "orders": orders})

@router.get("/product/add", response_class=HTMLResponse)
def add_product_page(request: Request):
    user = request.state.user
    if not user or not user.is_admin:
        return RedirectResponse(url="/catalog")
    return templates.TemplateResponse("product_form.html", {"request": request, "product": None})

@router.post("/product/add")
def add_product(request: Request, name: str = Form(...), description: str = Form(...), price: float = Form(...), stock: int = Form(...), image_url: str = Form(...), category: str = Form(...), db: Session = Depends(get_db)):
    user = request.state.user
    if not user or not user.is_admin:
        return RedirectResponse(url="/catalog")
    new_prod = Product(name=name, description=description, price=price, stock=stock, image_url=image_url, category=category)
    db.add(new_prod)
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@router.get("/product/edit/{product_id}", response_class=HTMLResponse)
def edit_product_page(request: Request, product_id: int, db: Session = Depends(get_db)):
    user = request.state.user
    if not user or not user.is_admin:
        return RedirectResponse(url="/catalog")
    product = db.query(Product).filter(Product.id == product_id).first()
    return templates.TemplateResponse("product_form.html", {"request": request, "product": product})

@router.post("/product/edit/{product_id}")
def edit_product(request: Request, product_id: int, name: str = Form(...), description: str = Form(...), price: float = Form(...), stock: int = Form(...), image_url: str = Form(...), category: str = Form(...), db: Session = Depends(get_db)):
    user = request.state.user
    if not user or not user.is_admin:
        return RedirectResponse(url="/catalog")
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

@router.post("/product/delete/{product_id}")
def delete_product(request: Request, product_id: int, db: Session = Depends(get_db)):
    user = request.state.user
    if not user or not user.is_admin:
        return RedirectResponse(url="/catalog")
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        db.delete(product)
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@router.post("/order/status/{order_id}")
def update_order_status(request: Request, order_id: int, status: str = Form(...), db: Session = Depends(get_db)):
    user = request.state.user
    if not user or not user.is_admin:
        return RedirectResponse(url="/catalog")
    order = db.query(Order).filter(Order.id == order_id).first()
    if order:
        order.status = status
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)