from pydantic import BaseModel, ConfigDict, Field


class CategoryResponse(BaseModel):
    id: int = Field(examples=[1])
    name: str = Field(examples=["Electronics"])
    slug: str = Field(examples=["electronics"])
    description: str | None = Field(
        default=None,
        examples=["Electronic devices and accessories"],
    )

    model_config = ConfigDict(from_attributes=True)


class ProductCategoryResponse(BaseModel):
    id: int = Field(examples=[1])
    name: str = Field(examples=["Electronics"])
    slug: str = Field(examples=["electronics"])

    model_config = ConfigDict(from_attributes=True)


class ProductResponse(BaseModel):
    id: int = Field(examples=[1])
    name: str = Field(examples=["Wireless Headphones"])
    description: str | None = Field(
        default=None,
        examples=["Bluetooth wireless headphones"],
    )
    price: float = Field(examples=[99.99])
    stock: int = Field(examples=[15])
    rating: float = Field(examples=[4.5])
    category: ProductCategoryResponse

    model_config = ConfigDict(from_attributes=True)