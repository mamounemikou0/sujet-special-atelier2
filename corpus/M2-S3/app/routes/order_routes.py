from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
import models
import auth
import re

router = APIRouter(prefix="/api/orders", tags=["orders"])


class CheckoutIn(BaseModel):
    shipping_address: str
    card_number: str  # Fake, 16-digit simulation


class StatusUpdate(BaseModel):
    status: models.OrderStatus


def order_to_dict(order: models.Order):
    return {
        "id": order.id,
        "status": order.status,
        "total": order.total,
        "shipping_address": order.shipping_address,
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat() if order.updated_at else None,
        "items": [
            {
                "id": i.id,
                "product_id": i.product_id,
                "product_name": i.product.name if i.product else "Deleted product",
                "product_image": i.product.image_url if i.product else "",
                "quantity": i.quantity,
                "unit_price": i.unit_price,
            }
            for i in order.items
        ],
        "user": {
            "id": order.user.id,
            "email": order.user.email,
            "full_name": order.user.full_name,
        } if order.user else None,
    }


@router.post("/checkout")
def checkout(
    data: CheckoutIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_user),
):
    # Validate fake card (16 digits)
    card = re.sub(r"\s+", "", data.card_number)
    if not re.match(r"^\d{16}$", card):
        raise HTTPException(status_code=400, detail="Card number must be exactly 16 digits")

    cart_items = db.query(models.CartItem).filter(models.CartItem.user_id == current_user.id).all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Verify stock and compute total
    total = 0.0
    for item in cart_items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not product or product.stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"Not enough stock for {product.name if product else 'product'}")
        total += product.price * item.quantity

    # Create order
    order = models.Order(
        user_id=current_user.id,
        total=round(total, 2),
        shipping_address=data.shipping_address,
    )
    db.add(order)
    db.flush()

    # Create order items and decrement stock
    for item in cart_items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        order_item = models.OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=product.price,
        )
        db.add(order_item)
        product.stock -= item.quantity

    # Clear cart
    db.query(models.CartItem).filter(models.CartItem.user_id == current_user.id).delete()

    db.commit()
    db.refresh(order)
    return order_to_dict(order)


@router.get("/my")
def my_orders(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_user),
):
    orders = (
        db.query(models.Order)
        .filter(models.Order.user_id == current_user.id)
        .order_by(models.Order.created_at.desc())
        .all()
    )
    return [order_to_dict(o) for o in orders]


@router.get("/all")
def all_orders(
    db: Session = Depends(get_db),
    _admin: models.User = Depends(auth.require_admin),
):
    orders = db.query(models.Order).order_by(models.Order.created_at.desc()).all()
    return [order_to_dict(o) for o in orders]


@router.put("/{order_id}/status")
def update_status(
    order_id: int,
    data: StatusUpdate,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(auth.require_admin),
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = data.status
    db.commit()
    db.refresh(order)
    return order_to_dict(order)
