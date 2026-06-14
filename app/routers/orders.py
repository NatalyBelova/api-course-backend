from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session, joinedload

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.models import CartItem, Order, OrderItem, OrderStatus, Product, User
from app.schemas.orders import OrderListItemResponse, OrderResponse

router = APIRouter(tags=["Orders"])


def build_order_response(order: Order) -> OrderResponse:
    items = []

    for item in order.items:
        item_total = float(item.price_at_purchase) * item.quantity

        items.append(
            {
                "product": {
                    "id": item.product.id,
                    "name": item.product.name,
                },
                "quantity": item.quantity,
                "price_at_purchase": float(item.price_at_purchase),
                "item_total": item_total,
            }
        )

    return OrderResponse(
        id=order.id,
        status=order.status,
        total_price=float(order.total_price),
        items=items,
        created_at=order.created_at,
        cancelled_at=order.cancelled_at,
        completed_at=order.completed_at,
    )


@router.post(
    "/orders",
    response_model=OrderResponse,
    status_code=201,
    summary="Create order from cart",
    description=(
        "Creates an order from the current user's cart and clears the cart after successful creation.\n\n"
        "Authorization is required.\n\n"
        "Business rules:\n"
        "- cart must not be empty\n"
        "- all products in cart must be active\n"
        "- requested quantity must not exceed current product stock\n"
        "- after successful order creation, the cart is cleared\n"
        "- order is created with status `created`"
    ),
    responses={
        201: {
            "description": "Order successfully created",
        },
        400: {
            "description": "Empty cart or not enough stock",
            "content": {
                "application/json": {
                    "examples": {
                        "empty_cart": {
                            "summary": "Empty cart",
                            "value": {"detail": "Cannot create order from empty cart"},
                        },
                        "not_enough_stock": {
                            "summary": "Not enough stock",
                            "value": {"detail": "Not enough stock for product: Gaming Keyboard"},
                        },
                    }
                }
            },
        },
        401: {
            "description": "Missing, invalid or inactive token",
        },
        404: {
            "description": "Product from cart was not found or became inactive",
            "content": {
                "application/json": {
                    "example": {"detail": "Product not found or inactive"}
                }
            },
        },
    },
)
def create_order(
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

    if not cart_items:
        raise HTTPException(status_code=400, detail="Cannot create order from empty cart")

    total_price = 0

    for cart_item in cart_items:
        product = cart_item.product

        if not product or not product.is_active:
            raise HTTPException(status_code=404, detail="Product not found or inactive")

        if cart_item.quantity > product.stock:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough stock for product: {product.name}",
            )

        total_price += float(product.price) * cart_item.quantity

    order = Order(
        user_id=current_user.id,
        status=OrderStatus.created.value,
        total_price=total_price,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    for cart_item in cart_items:
        product = cart_item.product

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=cart_item.quantity,
            price_at_purchase=product.price,
        )

        db.add(order_item)

    for cart_item in cart_items:
        db.delete(cart_item)

    db.commit()

    order = (
        db.query(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.product))
        .filter(Order.id == order.id)
        .first()
    )

    return build_order_response(order)


@router.get(
    "/orders",
    response_model=list[OrderListItemResponse],
    summary="Get current user's orders",
    description=(
        "Returns a list of orders for the current authenticated user.\n\n"
        "Authorization is required.\n\n"
        "Use this endpoint to check that an order was created successfully and belongs to the current user."
    ),
    responses={
        200: {
            "description": "Orders returned successfully",
        },
        401: {
            "description": "Missing, invalid or inactive token",
        },
    },
)
def get_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    orders = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.user_id == current_user.id)
        .order_by(Order.id)
        .all()
    )

    return [
        OrderListItemResponse(
            id=order.id,
            status=order.status,
            total_price=float(order.total_price),
            items_count=len(order.items),
            created_at=order.created_at,
        )
        for order in orders
    ]


@router.get(
    "/orders/{order_id}",
    response_model=OrderResponse,
    summary="Get order by id",
    description=(
        "Returns a specific order if it belongs to the current authenticated user.\n\n"
        "Authorization is required.\n\n"
        "Business rules:\n"
        "- order must exist\n"
        "- order must belong to the current user"
    ),
    responses={
        200: {
            "description": "Order returned successfully",
        },
        401: {
            "description": "Missing, invalid or inactive token",
        },
        403: {
            "description": "Order belongs to another user",
            "content": {
                "application/json": {
                    "example": {"detail": "You do not have access to this order"}
                }
            },
        },
        404: {
            "description": "Order not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Order not found"}
                }
            },
        },
        422: {
            "description": "Validation error. For example, order_id is not an integer.",
        },
    },
)
def get_order_by_id(
    order_id: int = Path(
        description="Order id.",
        examples=[1],
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = (
        db.query(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.product))
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this order")

    return build_order_response(order)


@router.patch(
    "/orders/{order_id}/cancel",
    response_model=OrderResponse,
    summary="Cancel order",
    description=(
        "Cancels an order if it belongs to the current user and has status `created`.\n\n"
        "Authorization is required.\n\n"
        "Allowed status transition:\n"
        "- created → cancelled\n\n"
        "Forbidden transitions:\n"
        "- cancelled → cancelled\n"
        "- completed → cancelled"
    ),
    responses={
        200: {
            "description": "Order cancelled successfully",
        },
        401: {
            "description": "Missing, invalid or inactive token",
        },
        403: {
            "description": "Order belongs to another user",
            "content": {
                "application/json": {
                    "example": {"detail": "You do not have access to this order"}
                }
            },
        },
        404: {
            "description": "Order not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Order not found"}
                }
            },
        },
        409: {
            "description": "Order status does not allow cancellation",
            "content": {
                "application/json": {
                    "examples": {
                        "already_cancelled": {
                            "summary": "Order is already cancelled",
                            "value": {"detail": "Order is already cancelled"},
                        },
                        "completed_order": {
                            "summary": "Completed order cannot be cancelled",
                            "value": {"detail": "Completed order cannot be cancelled"},
                        },
                    }
                }
            },
        },
        422: {
            "description": "Validation error. For example, order_id is not an integer.",
        },
    },
)
def cancel_order(
    order_id: int = Path(
        description="Order id.",
        examples=[1],
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = (
        db.query(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.product))
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this order")

    if order.status == OrderStatus.cancelled.value:
        raise HTTPException(status_code=409, detail="Order is already cancelled")

    if order.status == OrderStatus.completed.value:
        raise HTTPException(status_code=409, detail="Completed order cannot be cancelled")

    order.status = OrderStatus.cancelled.value
    order.cancelled_at = datetime.utcnow()

    db.commit()
    db.refresh(order)

    return build_order_response(order)


@router.patch(
    "/orders/{order_id}/complete",
    response_model=OrderResponse,
    summary="Complete order",
    description=(
        "Completes an order if it belongs to the current user and has status `created`.\n\n"
        "Authorization is required.\n\n"
        "Allowed status transition:\n"
        "- created → completed\n\n"
        "Forbidden transitions:\n"
        "- completed → completed\n"
        "- cancelled → completed"
    ),
    responses={
        200: {
            "description": "Order completed successfully",
        },
        401: {
            "description": "Missing, invalid or inactive token",
        },
        403: {
            "description": "Order belongs to another user",
            "content": {
                "application/json": {
                    "example": {"detail": "You do not have access to this order"}
                }
            },
        },
        404: {
            "description": "Order not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Order not found"}
                }
            },
        },
        409: {
            "description": "Order status does not allow completion",
            "content": {
                "application/json": {
                    "examples": {
                        "already_completed": {
                            "summary": "Order is already completed",
                            "value": {"detail": "Order is already completed"},
                        },
                        "cancelled_order": {
                            "summary": "Cancelled order cannot be completed",
                            "value": {"detail": "Cancelled order cannot be completed"},
                        },
                    }
                }
            },
        },
        422: {
            "description": "Validation error. For example, order_id is not an integer.",
        },
    },
)
def complete_order(
    order_id: int = Path(
        description="Order id.",
        examples=[1],
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = (
        db.query(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.product))
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this order")

    if order.status == OrderStatus.cancelled.value:
        raise HTTPException(status_code=409, detail="Cancelled order cannot be completed")

    if order.status == OrderStatus.completed.value:
        raise HTTPException(status_code=409, detail="Order is already completed")

    order.status = OrderStatus.completed.value
    order.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(order)

    return build_order_response(order)