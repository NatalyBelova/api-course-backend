from pydantic import BaseModel, Field


class ResetDeletedResponse(BaseModel):
    cart_items: int = Field(
        examples=[1],
        description="Number of deleted cart items for the current user.",
    )
    orders: int = Field(
        examples=[1],
        description="Number of deleted orders for the current user.",
    )
    order_items: int = Field(
        examples=[2],
        description="Number of deleted order items from the current user's orders.",
    )
    reviews: int = Field(
        examples=[1],
        description="Number of deleted reviews created by the current user.",
    )
    homework_results: int = Field(
        examples=[0],
        description="Number of deleted homework check results for the current user.",
    )


class ResetTestDataResponse(BaseModel):
    message: str = Field(examples=["Test data has been reset successfully"])
    deleted: ResetDeletedResponse