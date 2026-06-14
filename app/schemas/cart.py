from pydantic import BaseModel, ConfigDict, Field


class CartProductResponse(BaseModel):
    id: int = Field(examples=[2])
    name: str = Field(examples=["Gaming Keyboard"])
    price: float = Field(examples=[120.0])
    stock: int = Field(examples=[8])

    model_config = ConfigDict(from_attributes=True)


class CartItemResponse(BaseModel):
    id: int = Field(examples=[1])
    product: CartProductResponse
    quantity: int = Field(examples=[2])
    item_total: float = Field(examples=[240.0])

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    items: list[CartItemResponse]
    total_price: float = Field(examples=[240.0])


class AddCartItemRequest(BaseModel):
    product_id: int = Field(
        examples=[2],
        description="Product id from the catalog.",
    )
    quantity: int = Field(
        examples=[2],
        description="Product quantity. Must be greater than 0 and cannot exceed product stock.",
    )


class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(
        examples=[3],
        description="New product quantity. Must be greater than 0 and cannot exceed product stock.",
    )


class MessageResponse(BaseModel):
    message: str = Field(examples=["Cart item deleted successfully"])