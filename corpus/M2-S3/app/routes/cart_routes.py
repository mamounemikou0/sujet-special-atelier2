from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
import models
import auth

router = APIRouter(prefix="/api/cart", tags=["cart"])


class CartAddIn(BaseModel):
    product_id: int
    quantity: int = 1


class CartUpdateIn(BaseModel):
    quantity: int


def cart_to_dict(items):
    result = []
    for item in items:
        result.append({
            "id": item.id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "product": {
                "id": item.product.id,
                "name": item.product.name,
                "price": item.product.price,
                "image_url": item.product.image_url,
                "stock": item.product.stock,
            },
        })
    return result


@router.get("")
def get_cart(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_user),
):
    items = db.query(models.CartItem).filter(models.CartItem.user_id == current_user.id).all()
    return cart_to_dict(items)


@router.post("")
def add_to_cart(
    data: CartAddIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_user),
):
    product = db.query(models.Product).filter(models.Product.id == data.product_id).first()
    if not product or not product.is_active:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.stock < data.quantity:
        raise HTTPException(status_code=400, detail="Not enough stock")

    existing = db.query(models.CartItem).filter(
        models.CartItem.user_id == current_user.id,
        models.CartItem.product_id == data.product_id,
    ).first()

    if existing:
        new_qty = existing.quantity + data.quantity
        if product.stock < new_qty:
            raise HTTPException(status_code=400, detail="Not enough stock")
        existing.quantity = new_qty
    else:
        item = models.CartItem(user_id=current_user.id, product_id=data.product_id, quantity=data.quantity)
        db.add(item)

    db.commit()
    items = db.query(models.CartItem).filter(models.CartItem.user_id == current_user.id).all()
    return cart_to_dict(items)


@router.put("/{item_id}")
def update_cart_item(
    item_id: int,
    data: CartUpdateIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_user),
):
    item = db.query(models.CartItem).filter(
        models.CartItem.id == item_id,
        models.CartItem.user_id == current_user.id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    if data.quantity <= 0:
        db.delete(item)
    else:
        if item.product.stock < data.quantity:
            raise HTTPException(status_code=400, detail="Not enough stock")
        item.quantity = data.quantity
    db.commit()
    items = db.query(models.CartItem).filter(models.CartItem.user_id == current_user.id).all()
    return cart_to_dict(items)


@router.delete("/{item_id}")
def remove_cart_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_user),
):
    item = db.query(models.CartItem).filter(
        models.CartItem.id == item_id,
        models.CartItem.user_id == current_user.id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(item)
    db.commit()
    items = db.query(models.CartItem).filter(models.CartItem.user_id == current_user.id).all()
    return cart_to_dict(items)


@router.delete("")
def clear_cart(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_user),
):
    db.query(models.CartItem).filter(models.CartItem.user_id == current_user.id).delete()
    db.commit()
    return []
