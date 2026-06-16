from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from models import Product, Order, OrderStatus, get_db
from deps import require_admin

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="templates")


@router.get("/")
def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    product_count = db.query(Product).count()
    order_count = db.query(Order).count()
    return templates.TemplateResponse(
        "admin_dashboard.html",
        {
            "request": request,
            "user": admin,
            "product_count": product_count,
            "order_count": order_count,
        },
    )


@router.get("/products")
def admin_products(
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    products = db.query(Product).all()
    return templates.TemplateResponse(
        "admin_products.html",
        {"request": request, "user": admin, "products": products},
    )


@router.post("/products/add")
def admin_add_product(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),
    image_url: str = Form(""),
    category: str = Form(""),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    product = Product(
        name=name,
        description=description,
        price=price,
        stock=stock,
        image_url=image_url,
        category=category,
    )
    db.add(product)
    db.commit()
    return RedirectResponse(url="/admin/products", status_code=302)


@router.post("/products/update/{product_id}")
def admin_update_product(
    product_id: int,
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),
    image_url: str = Form(""),
    category: str = Form(""),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
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
    return RedirectResponse(url="/admin/products", status_code=302)


@router.post("/products/delete/{product_id}")
def admin_delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        db.delete(product)
        db.commit()
    return RedirectResponse(url="/admin/products", status_code=302)


@router.get("/orders")
def admin_orders(
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    orders = db.query(Order).order_by(Order.id.desc()).all()
    return templates.TemplateResponse(
        "admin_orders.html",
        {"request": request, "user": admin, "orders": orders, "OrderStatus": OrderStatus},
    )


@router.post("/orders/status/{order_id}")
def admin_update_order_status(
    order_id: int,
    status_value: str = Form(...),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if order and status_value in [s.value for s in OrderStatus]:
        order.status = OrderStatus(status_value)
        db.commit()
    return RedirectResponse(url="/admin/orders", status_code=302)
