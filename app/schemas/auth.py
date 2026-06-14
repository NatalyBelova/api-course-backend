from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserResponse(BaseModel):
    id: int = Field(examples=[1])
    name: str = Field(examples=["Ivan"])
    email: str = Field(examples=["ivan@example.com"])

    model_config = ConfigDict(from_attributes=True)


class RegisterRequest(BaseModel):
    name: str = Field(
        min_length=2,
        examples=["Ivan"],
        description="User name. Must contain at least 2 characters.",
    )
    email: EmailStr = Field(
        examples=["ivan@example.com"],
        description="User email. Must be a valid email address and must be unique.",
    )
    password: str = Field(
        min_length=6,
        examples=["password123"],
        description="User password. Must contain at least 6 characters.",
    )


class LoginRequest(BaseModel):
    email: EmailStr = Field(
        examples=["ivan@example.com"],
        description="Registered user email.",
    )
    password: str = Field(
        min_length=6,
        examples=["password123"],
        description="User password.",
    )


class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str = Field(
        examples=["course_abc123"],
        description="Access token. Use it in protected endpoints as Bearer token.",
    )
    token_type: str = Field(default="Bearer", examples=["Bearer"])


class LoginResponse(BaseModel):
    access_token: str = Field(
        examples=["course_abc123"],
        description="Access token. Use it in protected endpoints as Bearer token.",
    )
    token_type: str = Field(default="Bearer", examples=["Bearer"])