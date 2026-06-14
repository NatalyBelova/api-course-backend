from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.models import Category, Product
from app.schemas.products import CategoryResponse, ProductResponse

router = APIRouter(tags=["Products"])


@router.get(
    "/categories",
    response_model=list[CategoryResponse],
    summary="Get product categories",
    description=(
        "Returns all product categories.\n\n"
        "This endpoint does not require authorization.\n\n"
        "Use it before filtering products by category slug."
    ),
    responses={
        200: {
            "description": "Categories returned successfully",
        },
    },
)
def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.id).all()


@router.get(
    "/products",
    response_model=list[ProductResponse],
    summary="Get product list",
    description=(
        "Returns active products from the catalog.\n\n"
        "This endpoint does not require authorization.\n\n"
        "You can practice query parameters with this endpoint:\n"
        "- category: filter by category slug, for example electronics\n"
        "- min_price: return products with price greater than or equal to this value\n"
        "- max_price: return products with price less than or equal to this value\n"
        "- search: search products by name\n\n"
        "Inactive products are not returned."
    ),
    responses={
        200: {
            "description": "Products returned successfully",
        },
        400: {
            "description": "Invalid price range",
            "content": {
                "application/json": {
                    "example": {"detail": "min_price cannot be greater than max_price"}
                }
            },
        },
        422: {
            "description": "Validation error. For example, product_id or price parameter has invalid type.",
        },
    },
)
def get_products(
    category: str | None = Query(
        default=None,
        description="Filter products by category slug. Example: electronics",
        examples=["electronics"],
    ),
    min_price: Decimal | None = Query(
        default=None,
        ge=0,
        description="Minimum product price. Must be greater than or equal to 0.",
        examples=[50],
    ),
    max_price: Decimal | None = Query(
        default=None,
        ge=0,
        description="Maximum product price. Must be greater than or equal to 0.",
        examples=[150],
    ),
    search: str | None = Query(
        default=None,
        description="Search by product name. Example: keyboard",
        examples=["keyboard"],
    ),
    db: Session = Depends(get_db),
):
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=400,
            detail="min_price cannot be greater than max_price",
        )

    query = (
        db.query(Product)
        .options(joinedload(Product.category))
        .filter(Product.is_active.is_(True))
    )

    if category:
        query = query.join(Category).filter(Category.slug == category)

    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    return query.order_by(Product.id).all()


@router.get(
    "/products/{product_id}",
    response_model=ProductResponse,
    summary="Get product by id",
    description=(
        "Returns one active product by product_id.\n\n"
        "This endpoint does not require authorization.\n\n"
        "Use this endpoint to practice path parameters.\n\n"
        "If the product does not exist or is inactive, the API returns 404."
    ),
    responses={
        200: {
            "description": "Product returned successfully",
        },
        404: {
            "description": "Product not found or inactive",
            "content": {
                "application/json": {
                    "example": {"detail": "Product not found"}
                }
            },
        },
        422: {
            "description": "Validation error. For example, product_id is not an integer.",
        },
    },
)
def get_product_by_id(
    product_id: int = Path(
        description="Product id from the catalog.",
        examples=[1],
    ),
    db: Session = Depends(get_db),
):
    product = (
        db.query(Product)
        .options(joinedload(Product.category))
        .filter(Product.id == product_id, Product.is_active.is_(True))
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product