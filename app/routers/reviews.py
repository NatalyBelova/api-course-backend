from fastapi import APIRouter, Body, Depends, HTTPException, Path
from sqlalchemy.orm import Session, joinedload

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.models import Product, Review, User
from app.schemas.reviews import CreateReviewRequest, ReviewResponse

router = APIRouter(tags=["Reviews"])


@router.get(
    "/products/{product_id}/reviews",
    response_model=list[ReviewResponse],
    summary="Get product reviews",
    description=(
        "Returns reviews for a specific active product.\n\n"
        "This endpoint does not require authorization.\n\n"
        "Business rules:\n"
        "- product must exist\n"
        "- product must be active\n"
        "- if the product has no reviews, the API returns an empty list"
    ),
    responses={
        200: {
            "description": "Product reviews returned successfully",
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
def get_product_reviews(
    product_id: int = Path(
        description="Product id from the catalog.",
        examples=[1],
    ),
    db: Session = Depends(get_db),
):
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.is_active.is_(True))
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    reviews = (
        db.query(Review)
        .options(joinedload(Review.user))
        .filter(Review.product_id == product_id)
        .order_by(Review.id)
        .all()
    )

    return reviews


@router.post(
    "/products/{product_id}/reviews",
    response_model=ReviewResponse,
    status_code=201,
    summary="Create product review",
    description=(
        "Creates a review for a specific active product.\n\n"
        "Authorization is required.\n\n"
        "Business rules:\n"
        "- product must exist\n"
        "- product must be active\n"
        "- rating must be between 1 and 5\n"
        "- text is optional\n"
        "- one user can create only one review per product"
    ),
    responses={
        201: {
            "description": "Review successfully created",
        },
        400: {
            "description": "Invalid rating",
            "content": {
                "application/json": {
                    "examples": {
                        "rating_too_low": {
                            "summary": "Rating is less than 1",
                            "value": {"detail": "Rating must be between 1 and 5"},
                        },
                        "rating_too_high": {
                            "summary": "Rating is greater than 5",
                            "value": {"detail": "Rating must be between 1 and 5"},
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
            "description": "User has already reviewed this product",
            "content": {
                "application/json": {
                    "example": {"detail": "You have already reviewed this product"}
                }
            },
        },
        422: {
            "description": "Validation error. For example, product_id or rating has invalid type.",
        },
    },
)
def create_product_review(
    product_id: int = Path(
        description="Product id from the catalog.",
        examples=[1],
    ),
    payload: CreateReviewRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.is_active.is_(True))
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if payload.rating < 1 or payload.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    existing_review = (
        db.query(Review)
        .filter(
            Review.user_id == current_user.id,
            Review.product_id == product_id,
        )
        .first()
    )

    if existing_review:
        raise HTTPException(
            status_code=409,
            detail="You have already reviewed this product",
        )

    review = Review(
        user_id=current_user.id,
        product_id=product_id,
        rating=payload.rating,
        text=payload.text,
    )

    db.add(review)
    db.commit()
    db.refresh(review)

    review = (
        db.query(Review)
        .options(joinedload(Review.user))
        .filter(Review.id == review.id)
        .first()
    )

    return review