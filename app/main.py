from fastapi import FastAPI

from app.routers import auth, buggy, cart, orders, products, reviews, test_data

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
)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(reviews.router)
app.include_router(test_data.router)
app.include_router(buggy.router)


@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
    description="Returns API status. Use this endpoint to check that the backend is running.",
)
def health_check():
    return {"status": "ok"}