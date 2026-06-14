from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session, joinedload

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.models import CartItem, Category, Order, OrderItem, OrderStatus, Product, User
from app.schemas.cart import AddCartItemRequest, CartItemResponse
from app.schemas.orders import OrderResponse
from app.schemas.products import ProductResponse

router = APIRouter(tags=["Buggy Endpoints"])


@router.get(
    "/buggy/products",
    summary="Bug hunting: get products",
    description=(
        "Training endpoint for bug hunting practice.\n\n"
        "This endpoint looks similar to `GET /products`, but it may behave differently.\n\n"
        "Task for students:\n"
        "- send different combinations of query parameters\n"
        "- compare actual results with the documented behavior of `GET /products`\n"
        "- identify inconsistencies\n"
        "- write bug reports for any issues found\n\n"
        "This endpoint does not require authorization."
    ),
    responses={
        200: {
            "description": "Products returned. Analyze the response carefully and compare it with GET /products.",
        },
        422: {
            "description": "Validation error. For example, query parameter has invalid type.",
        },
    },
)
def get_buggy_products(
    category: str | None = Query(
        default=None,
        description="Filter products by category slug. Example: electronics",
        examples=["electronics"],
    ),
    min_price: float | None = Query(
        default=None,
        ge=0,
        description="Minimum product price.",
        examples=[50],
    ),
    max_price: float | None = Query(
        default=None,
        ge=0,
        description="Maximum product price.",
        examples=[150],
    ),
    search: str | None = Query(
        default=None,
        description="Search by product name. Example: keyboard",
        examples=["keyboard"],
    ),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Product)
        .options(joinedload(Product.category))
    )

    # BUG 1: inactive products are not filtered out
    # Expected: Product.is_active == True

    if category:
        query = query.join(Category).filter(Category.slug == category)

    # BUG 2: max_price filter is ignored
    # Expected: if max_price is provided, Product.price <= max_price

    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    products = query.order_by(Product.id).all()

    # BUG 3: price and rating are returned as strings
    # Expected: price and rating should be numbers
    return [
        {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": str(product.price),
            "stock": product.stock,
            "rating": str(product.rating),
            "is_active": product.is_active,
            "category": {
                "id": product.category.id,
                "name": product.category.name,
                "slug": product.category.slug,
            },
        }
        for product in products
    ]


@router.post(
    "/buggy/cart/items",
    response_model=CartItemResponse,
    summary="Bug hunting: add product to cart",
    description=(
        "Training endpoint for bug hunting practice.\n\n"
        "This endpoint looks similar to `POST /cart/items`, but it may behave differently.\n\n"
        "Task for students:\n"
        "- test valid and invalid request bodies\n"
        "- compare actual results with the documented behavior of `POST /cart/items`\n"
        "- check status codes, response body and business rules\n"
        "- write bug reports for any issues found\n\n"
        "Authorization is required."
    ),
    responses={
        200: {
            "description": "Response returned. Analyze whether the status code and response match expected API behavior.",
        },
        400: {
            "description": "Bad request. Analyze whether the error response is correct.",
        },
        401: {
            "description": "Missing, invalid or inactive token.",
        },
        404: {
            "description": "Product was not found. Analyze whether the error response is correct.",
        },
        409: {
            "description": "Conflict. Analyze whether the business rule is handled correctly.",
        },
        422: {
            "description": "Validation error. For example, product_id or quantity has invalid type.",
        },
    },
)
def add_buggy_cart_item(
    payload: AddCartItemRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = (
        db.query(Product)
        .filter(Product.id == payload.product_id, Product.is_active.is_(True))
        .first()
    )

    # BUG 1: bad error response for missing product
    # Expected: 404 with {"detail": "Product not found"}
    if not product:
        raise HTTPException(status_code=404, detail={"error": True})

    # BUG 2: quantity = -1 is accepted
    # Expected: quantity <= 0 should return 400
    if payload.quantity == 0:
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

    item_total = float(cart_item.product.price) * cart_item.quantity

    # BUG 3: endpoint creates resource but will return 200 by default
    # Expected: 201 Created
    return {
        "id": cart_item.id,
        "product": {
            "id": cart_item.product.id,
            "name": cart_item.product.name,
            "price": float(cart_item.product.price),
            "stock": cart_item.product.stock,
        },
        "quantity": cart_item.quantity,
        "item_total": item_total,
    }


@router.patch(
    "/buggy/orders/{order_id}/cancel",
    response_model=OrderResponse,
    summary="Bug hunting: cancel order",
    description=(
        "Training endpoint for bug hunting practice.\n\n"
        "This endpoint looks similar to `PATCH /orders/{order_id}/cancel`, "
        "but it may behave differently.\n\n"
        "Task for students:\n"
        "- create orders with different statuses\n"
        "- try to cancel orders in different states\n"
        "- compare actual behavior with the documented behavior of the normal Orders API\n"
        "- check status codes, response body and status transitions\n"
        "- write bug reports for any issues found\n\n"
        "Authorization is required."
    ),
    responses={
        200: {
            "description": "Response returned. Analyze whether the order transition is correct.",
        },
        401: {
            "description": "Missing, invalid or inactive token.",
        },
        403: {
            "description": "Access issue. Analyze whether ownership rules are handled correctly.",
        },
        404: {
            "description": "Order not found.",
        },
        409: {
            "description": "Conflict. Analyze whether the order status transition is handled correctly.",
        },
        422: {
            "description": "Validation error. For example, order_id is not an integer.",
        },
    },
)
def cancel_buggy_order(
    order_id: int = Path(
        description="Order id.",
        examples=[1],
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # BUG 1: ownership check is missing
    # Expected: if order.user_id != current_user.id -> 403

    # BUG 2: completed order can be cancelled
    # Expected: completed order should return 409

    # BUG 3: already cancelled order returns 200 instead of 409
    # Expected: already cancelled order should return 409

    order.status = OrderStatus.cancelled.value
    order.cancelled_at = order.updated_at

    db.commit()
    db.refresh(order)

    order = (
        db.query(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.product))
        .filter(Order.id == order.id)
        .first()
    )

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

    return {
        "id": order.id,
        "status": order.status,
        "total_price": float(order.total_price),
        "items": items,
        "created_at": order.created_at,
        "cancelled_at": order.cancelled_at,
        "completed_at": order.completed_at,
    }