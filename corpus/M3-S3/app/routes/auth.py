from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from models import SessionLocal, User
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["Authentication"])
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if request.state.user:
        return RedirectResponse(url="/catalog")
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email, User.password == password).first()
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Identifiants incorrects."})
    response = RedirectResponse(url="/catalog", status_code=303)
    response.set_cookie(key="user_id", value=str(user.id))
    return response

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
def register(request: Request, email: str = Form(...), password: str = Form(...), address: str = Form(...), db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Cet email est déjà pris."})
    new_user = User(email=email, password=password, shipping_address=address, is_admin=False)
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/auth/login", status_code=303)

@router.get("/logout")
def logout():
    response = RedirectResponse(url="/catalog")
    response.delete_cookie("user_id")
    return response