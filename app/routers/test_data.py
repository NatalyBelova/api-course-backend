from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.models import CartItem, HomeworkResult, Order, OrderItem, Review, User
from app.schemas.test_data import ResetTestDataResponse

router = APIRouter(tags=["Test Data"])


@router.post(
    "/test-data/reset",
    response_model=ResetTestDataResponse,
    summary="Reset current user's test data",
    description=(
        "Deletes only the current user's practice data.\n\n"
        "Authorization is required.\n\n"
        "This endpoint is useful when you want to restart the training scenario from a clean state.\n\n"
        "Deleted data:\n"
        "- cart items of the current user\n"
        "- orders of the current user\n"
        "- order items inside the current user's orders\n"
        "- reviews created by the current user\n"
        "- homework check results of the current user\n\n"
        "Data that is NOT deleted:\n"
        "- user account\n"
        "- active tokens\n"
        "- product catalog\n"
        "- categories"
    ),
    responses={
        200: {
            "description": "Current user's test data was reset successfully",
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
                        "inactive_token": {
                            "summary": "Inactive token",
                            "value": {"detail": "Token is inactive"},
                        },
                    }
                }
            },
        },
    },
)
def reset_test_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_order_ids = [
        order_id
        for (order_id,) in db.query(Order.id)
        .filter(Order.user_id == current_user.id)
        .all()
    ]

    deleted_order_items = 0

    if user_order_ids:
        deleted_order_items = (
            db.query(OrderItem)
            .filter(OrderItem.order_id.in_(user_order_ids))
            .delete(synchronize_session=False)
        )

    deleted_orders = (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .delete(synchronize_session=False)
    )

    deleted_cart_items = (
        db.query(CartItem)
        .filter(CartItem.user_id == current_user.id)
        .delete(synchronize_session=False)
    )

    deleted_reviews = (
        db.query(Review)
        .filter(Review.user_id == current_user.id)
        .delete(synchronize_session=False)
    )

    deleted_homework_results = (
        db.query(HomeworkResult)
        .filter(HomeworkResult.user_id == current_user.id)
        .delete(synchronize_session=False)
    )

    db.commit()

    return {
        "message": "Test data has been reset successfully",
        "deleted": {
            "cart_items": deleted_cart_items,
            "orders": deleted_orders,
            "order_items": deleted_order_items,
            "reviews": deleted_reviews,
            "homework_results": deleted_homework_results,
        },
    }