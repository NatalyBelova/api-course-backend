from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.utils import generate_token, hash_password, verify_password
from app.database import get_db
from app.models.models import Token, User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    UserResponse,
)

router = APIRouter(tags=["Auth"])


@router.post(
    "/auth/register",
    response_model=AuthResponse,
    status_code=201,
    summary="Register a new user",
    description=(
        "Creates a new user and returns an access token.\n\n"
        "Use this token for protected endpoints such as cart, orders, reviews and test data reset.\n\n"
        "Validation rules:\n"
        "- name must contain at least 2 characters\n"
        "- email must be valid and unique\n"
        "- password must contain at least 6 characters"
    ),
    responses={
        201: {
            "description": "User successfully registered",
        },
        400: {
            "description": "User with this email already exists",
            "content": {
                "application/json": {
                    "example": {"detail": "User with this email already exists"}
                }
            },
        },
        422: {
            "description": "Validation error",
        },
    },
)
def register_user(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
):
    existing_user = db.query(User).filter(User.email == payload.email).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists",
        )

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = Token(
        user_id=user.id,
        token=generate_token(),
        is_active=True,
    )

    db.add(token)
    db.commit()
    db.refresh(token)

    return {
        "user": user,
        "access_token": token.token,
        "token_type": "Bearer",
    }


@router.post(
    "/auth/login",
    response_model=LoginResponse,
    summary="Login user",
    description=(
        "Checks email and password and returns a new access token.\n\n"
        "A new token is created on every successful login. "
        "You can use the latest token for protected endpoints."
    ),
    responses={
        200: {
            "description": "Login successful",
        },
        401: {
            "description": "Invalid email or password",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid email or password"}
                }
            },
        },
        422: {
            "description": "Validation error",
        },
    },
)
def login_user(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    token = Token(
        user_id=user.id,
        token=generate_token(),
        is_active=True,
    )

    db.add(token)
    db.commit()
    db.refresh(token)

    return {
        "access_token": token.token,
        "token_type": "Bearer",
    }


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description=(
        "Returns the current user by Bearer token.\n\n"
        "In Swagger, click the Authorize button and paste your access token.\n\n"
        "In Postman, send the token in Authorization header:\n"
        "`Authorization: Bearer <access_token>`"
    ),
    responses={
        200: {
            "description": "Current user returned successfully",
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
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user