from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
import models
import auth

router = APIRouter(prefix="/api/products", tags=["products"])


class ProductIn(BaseModel):
    name: str
    description: str = ""
    price: float
    stock: int = 0
    image_url: str = ""
    category_id: Optional[int] = None
    is_active: bool = True


def product_to_dict(p: models.Product):
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "price": p.price,
        "stock": p.stock,
        "image_url": p.image_url,
        "category": {"id": p.category.id, "name": p.category.name} if p.category else None,
        "is_active": p.is_active,
    }


@router.get("")
def list_products(
    q: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(models.Product).filter(models.Product.is_active == True)
    if q:
        query = query.filter(models.Product.name.ilike(f"%{q}%"))
    if category_id:
        query = query.filter(models.Product.category_id == category_id)
    products = query.all()
    return [product_to_dict(p) for p in products]


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    cats = db.query(models.Category).all()
    return [{"id": c.id, "name": c.name, "slug": c.slug} for c in cats]


@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    p = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return product_to_dict(p)


@router.post("")
def create_product(
    data: ProductIn,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(auth.require_admin),
):
    product = models.Product(**data.dict())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product_to_dict(product)


@router.put("/{product_id}")
def update_product(
    product_id: int,
    data: ProductIn,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(auth.require_admin),
):
    p = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    for k, v in data.dict().items():
        setattr(p, k, v)
    db.commit()
    return product_to_dict(p)


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(auth.require_admin),
):
    p = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(p)
    db.commit()
    return {"ok": True}
