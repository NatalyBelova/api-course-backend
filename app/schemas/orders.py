from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrderProductResponse(BaseModel):
    id: int = Field(examples=[2])
    name: str = Field(examples=["Gaming Keyboard"])

    model_config = ConfigDict(from_attributes=True)


class OrderItemResponse(BaseModel):
    product: OrderProductResponse
    quantity: int = Field(examples=[2])
    price_at_purchase: float = Field(
        examples=[120.0],
        description="Product price at the moment when the order was created.",
    )
    item_total: float = Field(
        examples=[240.0],
        description="Item total price: price_at_purchase multiplied by quantity.",
    )

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: int = Field(examples=[1])
    status: str = Field(
        examples=["created"],
        description="Order status. Possible values: created, cancelled, completed.",
    )
    total_price: float = Field(examples=[240.0])
    items: list[OrderItemResponse]
    created_at: datetime
    cancelled_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)

    model_config = ConfigDict(from_attributes=True)


class OrderListItemResponse(BaseModel):
    id: int = Field(examples=[1])
    status: str = Field(
        examples=["created"],
        description="Order status. Possible values: created, cancelled, completed.",
    )
    total_price: float = Field(examples=[240.0])
    items_count: int = Field(examples=[1])
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)