from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewUserResponse(BaseModel):
    id: int = Field(examples=[1])
    name: str = Field(examples=["Ivan"])

    model_config = ConfigDict(from_attributes=True)


class ReviewResponse(BaseModel):
    id: int = Field(examples=[1])
    product_id: int = Field(examples=[1])
    rating: int = Field(
        examples=[5],
        description="Review rating. Possible values: 1, 2, 3, 4, 5.",
    )
    text: str | None = Field(
        default=None,
        examples=["Great product"],
        description="Optional review text.",
    )
    user: ReviewUserResponse
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CreateReviewRequest(BaseModel):
    rating: int = Field(
        ge=1,
        le=5,
        examples=[5],
        description="Review rating. Must be between 1 and 5.",
    )
    text: str | None = Field(
        default=None,
        max_length=500,
        description="Optional review text. Maximum 500 characters.",
        examples=["Great product"],
    )