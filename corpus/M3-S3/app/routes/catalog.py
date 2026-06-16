from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from models import SessionLocal, Product, Order
from sqlalchemy.orm import Session

router = APIRouter(prefix="/catalog", tags=["Catalog"])
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("", response_class=HTMLResponse)
def index(request: Request, search: str = None, category: str = None, db: Session = Depends(get_db)):
    query = db.query(Product)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    if category:
        query = query.filter(Product.category == category)
    products = query.all()
    categories = [c[0] for c in db.query(Product.category).distinct().all()]
    
    return templates.TemplateResponse("catalog.html", {
        "request": request, 
        "products": products, 
        "categories": categories,
        "search": search or "",
        "selected_category": category or ""
    })

@router.get("/orders", response_class=HTMLResponse)
def user_orders(request: Request, db: Session = Depends(get_db)):
    user = request.state.user
    if not user:
        return RedirectResponse(url="/auth/login")
    orders = db.query(Order).filter(Order.user_id == user.id).order_by(Order.created_at.desc()).all()
    return templates.TemplateResponse("orders.html", {"request": request, "orders": orders})