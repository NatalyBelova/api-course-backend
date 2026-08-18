import secrets

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.config import settings
from app.routers import auth, buggy, cart, homework, orders, products, reviews, test_data
from app.schemas.system import HealthResponse

tags_metadata = [
    {
        "name": "System",
        "description": "Service health check. Use it to verify that the API is running.",
    },
    {
        "name": "Auth",
        "description": (
            "User registration, login and current user profile. "
            "Use these endpoints to get an access token for protected methods."
        ),
    },
    {
        "name": "Products",
        "description": (
            "Product catalog endpoints. These methods do not require authorization. "
            "Use them to practice GET requests, path parameters and query parameters."
        ),
    },
    {
        "name": "Cart",
        "description": (
            "Shopping cart endpoints. These methods require Bearer token authorization. "
            "Use them to practice POST, PATCH, DELETE requests and request body validation."
        ),
    },
    {
        "name": "Orders",
        "description": (
            "Order endpoints. These methods require Bearer token authorization. "
            "Use them to practice business flow testing and status transitions."
        ),
    },
    {
        "name": "Reviews",
        "description": (
            "Product review endpoints. GET reviews is public, but creating a review requires authorization."
        ),
    },
    {
        "name": "Homework",
        "description": (
            "AI-graded homework submission. Submit the filled checks table for a practice and "
            "get back a score, a pass/needs_revision verdict and per-criterion feedback. "
            "Requires Bearer token authorization."
        ),
    },
    {
        "name": "Test Data",
        "description": (
            "Utility endpoint for cleaning the current user's test data. "
            "Use it when you want to restart the practice scenario."
        ),
    },
    {
        "name": "Buggy Endpoints",
        "description": (
            "Special training endpoints with intentional bugs. "
            "Use them to practice bug hunting and writing bug reports."
        ),
    },
]

app = FastAPI(
    title="API Course E-commerce Backend",
    description=(
        "Training API for learning API testing with Swagger and Postman.\n\n"
        "Main scenario: register a user, get a token, browse products, add products to cart, "
        "create orders, write reviews and practice negative checks.\n\n"
        "Protected endpoints require Bearer token authorization."
    ),
    version="0.1.0",
    openapi_tags=tags_metadata,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

security = HTTPBasic()


def verify_docs_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(
        credentials.username, settings.DOCS_USERNAME
    )
    correct_password = secrets.compare_digest(
        credentials.password, settings.DOCS_PASSWORD
    )

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username


app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(reviews.router)
app.include_router(homework.router)
app.include_router(test_data.router)
app.include_router(buggy.router)


@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
    description="Returns API status. Use this endpoint to check that the backend is running.",
    response_model=HealthResponse,
)
def health_check():
    return {"status": "ok"}


@app.get("/openapi.json", include_in_schema=False)
def get_openapi_json(username: str = Depends(verify_docs_credentials)):
    return get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
    )


@app.get("/docs", include_in_schema=False)
def get_docs(username: str = Depends(verify_docs_credentials)):
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{app.title} - Swagger UI",
    )


@app.get("/redoc", include_in_schema=False)
def get_redoc(username: str = Depends(verify_docs_credentials)):
    return get_redoc_html(
        openapi_url="/openapi.json",
        title=f"{app.title} - ReDoc",
    )