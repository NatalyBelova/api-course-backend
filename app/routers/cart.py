from fastapi import APIRouter, Body, Depends, HTTPException, Path
from sqlalchemy.orm import Session, joinedload

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.models import CartItem, Product, User
from app.schemas.cart import (
    AddCartItemRequest,
    CartItemResponse,
    CartResponse,
    MessageResponse,
    UpdateCartItemRequest,
)

router = APIRouter(tags=["Cart"])


def build_cart_item_response(cart_item: CartItem) -> CartItemResponse:
    product = cart_item.product
    item_total = float(product.price) * cart_item.quantity

    return CartItemResponse(
        id=cart_item.id,
        product={
            "id": product.id,
            "name": product.name,
            "price": float(product.price),
            "stock": product.stock,
        },
        quantity=cart_item.quantity,
        item_total=item_total,
    )


@router.get(
    "/cart",
    response_model=CartResponse,
    summary="Get current user's cart",
    description=(
        "Returns cart items for the current authenticated user.\n\n"
        "Authorization is required.\n\n"
        "In Swagger, click the Authorize button and paste your access token.\n\n"
        "In Postman, send the token in Authorization header:\n"
        "`Authorization: Bearer <access_token>`"
    ),
    responses={
        200: {
            "description": "Cart returned successfully",
        },
        401: {
            "description": "Missing, invalid or inactive token",
            "content": {
                "application/json": {
                    "examples": {
                        "missing_token": {
                            "summary": "Missing token",
                            "value": {"detail": "Authorization header is missing"},
                        },
                        "invalid_token": {
                            "summary": "Invalid token",
                            "value": {"detail": "Invalid token"},
                        },
                    }
                }
            },
        },
    },
)
def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart_items = (
        db.query(CartItem)
        .options(joinedload(CartItem.product))
        .filter(CartItem.user_id == current_user.id)
        .order_by(CartItem.id)
        .all()
    )

    items = [build_cart_item_response(item) for item in cart_items]
    total_price = sum(item.item_total for item in items)

    return CartResponse(
        items=items,
        total_price=total_price,
    )


@router.post(
    "/cart/items",
    response_model=CartItemResponse,
    status_code=201,
    summary="Add product to cart",
    description=(
        "Adds an active product to the current user's cart.\n\n"
        "Authorization is required.\n\n"
        "Business rules:\n"
        "- product_id must belong to an active product\n"
        "- quantity must be greater than 0\n"
        "- quantity cannot exceed product stock\n"
        "- the same product cannot be added twice to the same user's cart"
    ),
    responses={
        201: {
            "description": "Product successfully added to cart",
        },
        400: {
            "description": "Invalid quantity or not enough stock",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_quantity": {
                            "summary": "Quantity is zero or negative",
                            "value": {"detail": "Quantity must be greater than 0"},
                        },
                        "not_enough_stock": {
                            "summary": "Requested quantity exceeds available stock",
                            "value": {"detail": "Requested quantity exceeds available stock"},
                        },
                    }
                }
            },
        },
        401: {
            "description": "Missing, invalid or inactive token",
        },
        404: {
            "description": "Product not found or inactive",
            "content": {
                "application/json": {
                    "example": {"detail": "Product not found"}
                }
            },
        },
        409: {
            "description": "Product already exists in cart",
            "content": {
                "application/json": {
                    "example": {"detail": "Product already exists in cart"}
                }
            },
        },
        422: {
            "description": "Validation error. For example, product_id or quantity has invalid type.",
        },
    },
)
def add_cart_item(
    payload: AddCartItemRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = (
        db.query(Product)
        .filter(Product.id == payload.product_id, Product.is_active.is_(True))
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if payload.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than 0")

    if payload.quantity > product.stock:
        raise HTTPException(
            status_code=400,
            detail="Requested quantity exceeds available stock",
        )

    existing_cart_item = (
        db.query(CartItem)
        .filter(
            CartItem.user_id == current_user.id,
            CartItem.product_id == payload.product_id,
        )
        .first()
    )

    if existing_cart_item:
        raise HTTPException(status_code=409, detail="Product already exists in cart")

    cart_item = CartItem(
        user_id=current_user.id,
        product_id=payload.product_id,
        quantity=payload.quantity,
    )

    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)

    cart_item = (
        db.query(CartItem)
        .options(joinedload(CartItem.product))
        .filter(CartItem.id == cart_item.id)
        .first()
    )

    return build_cart_item_response(cart_item)


@router.patch(
    "/cart/items/{cart_item_id}",
    response_model=CartItemResponse,
    summary="Update cart item quantity",
    description=(
        "Updates quantity for a cart item that belongs to the current user.\n\n"
        "Authorization is required.\n\n"
        "Business rules:\n"
        "- cart item must exist\n"
        "- cart item must belong to the current user\n"
        "- quantity must be greater than 0\n"
        "- quantity cannot exceed product stock"
    ),
    responses={
        200: {
            "description": "Cart item updated successfully",
        },
        400: {
            "description": "Invalid quantity or not enough stock",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_quantity": {
                            "summary": "Quantity is zero or negative",
                            "value": {"detail": "Quantity must be greater than 0"},
                        },
                        "not_enough_stock": {
                            "summary": "Requested quantity exceeds available stock",
                            "value": {"detail": "Requested quantity exceeds available stock"},
                        },
                    }
                }
            },
        },
        401: {
            "description": "Missing, invalid or inactive token",
        },
        403: {
            "description": "Cart item belongs to another user",
            "content": {
                "application/json": {
                    "example": {"detail": "You do not have access to this cart item"}
                }
            },
        },
        404: {
            "description": "Cart item not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Cart item not found"}
                }
            },
        },
        422: {
            "description": "Validation error. For example, cart_item_id or quantity has invalid type.",
        },
    },
)
def update_cart_item(
    cart_item_id: int = Path(
        description="Cart item id.",
        examples=[1],
    ),
    payload: UpdateCartItemRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart_item = (
        db.query(CartItem)
        .options(joinedload(CartItem.product))
        .filter(CartItem.id == cart_item_id)
        .first()
    )

    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    if cart_item.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this cart item",
        )

    if payload.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than 0")

    if payload.quantity > cart_item.product.stock:
        raise HTTPException(
            status_code=400,
            detail="Requested quantity exceeds available stock",
        )

    cart_item.quantity = payload.quantity

    db.commit()
    db.refresh(cart_item)

    return build_cart_item_response(cart_item)


@router.delete(
    "/cart/items/{cart_item_id}",
    response_model=MessageResponse,
    summary="Delete cart item",
    description=(
        "Deletes a cart item that belongs to the current user.\n\n"
        "Authorization is required.\n\n"
        "Business rules:\n"
        "- cart item must exist\n"
        "- cart item must belong to the current user"
    ),
    responses={
        200: {
            "description": "Cart item deleted successfully",
        },
        401: {
            "description": "Missing, invalid or inactive token",
        },
        403: {
            "description": "Cart item belongs to another user",
            "content": {
                "application/json": {
                    "example": {"detail": "You do not have access to this cart item"}
                }
            },
        },
        404: {
            "description": "Cart item not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Cart item not found"}
                }
            },
        },
        422: {
            "description": "Validation error. For example, cart_item_id is not an integer.",
        },
    },
)
def delete_cart_item(
    cart_item_id: int = Path(
        description="Cart item id.",
        examples=[1],
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart_item = db.query(CartItem).filter(CartItem.id == cart_item_id).first()

    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    if cart_item.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this cart item",
        )

    db.delete(cart_item)
    db.commit()

    return {"message": "Cart item deleted successfully"}