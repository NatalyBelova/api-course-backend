# API Course Backend

Training backend for learning API testing with Swagger and Postman.

The project is a simple e-commerce API that allows students to practice:

* HTTP methods: GET, POST, PATCH, DELETE
* path parameters
* query parameters
* request body
* Bearer token authorization
* positive and negative API checks
* business flow testing
* bug hunting

## Main user flow

Student can practice the following scenario:

1. Register a user
2. Login and get an access token
3. Open product catalog
4. Add products to cart
5. Create an order from cart
6. Check order status
7. Cancel or complete an order
8. Create product reviews
9. Reset personal test data
10. Use buggy endpoints to practice finding API bugs

## API documentation

Swagger UI is available at:

```text
/docs
```

OpenAPI schema is available at:

```text
/openapi.json
```

## Main API sections

### System

* `GET /health`

### Auth

* `POST /auth/register`
* `POST /auth/login`
* `GET /me`

### Products

* `GET /categories`
* `GET /products`
* `GET /products/{product_id}`

### Cart

* `GET /cart`
* `POST /cart/items`
* `PATCH /cart/items/{cart_item_id}`
* `DELETE /cart/items/{cart_item_id}`

### Orders

* `POST /orders`
* `GET /orders`
* `GET /orders/{order_id}`
* `PATCH /orders/{order_id}/cancel`
* `PATCH /orders/{order_id}/complete`

### Reviews

* `GET /products/{product_id}/reviews`
* `POST /products/{product_id}/reviews`

### Test Data

* `POST /test-data/reset`

### Buggy Endpoints

Special endpoints for bug hunting practice:

* `GET /buggy/products`
* `POST /buggy/cart/items`
* `PATCH /buggy/orders/{order_id}/cancel`

Students should compare these endpoints with the regular API behavior and identify inconsistencies.

## Authorization

Protected endpoints require Bearer token authorization.

In Swagger:

```text
Click Authorize and paste the access token
```

In Postman:

```text
Authorization: Bearer <access_token>
```

## Tech stack

* Python
* FastAPI
* PostgreSQL
* SQLAlchemy
* Alembic
* Pydantic
* Docker Compose

## Local development

Create and activate virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start PostgreSQL:

```bash
docker compose up -d
```

Run migrations:

```bash
alembic upgrade head
```

Seed test data:

```bash
python -m app.seed
```

Run the server:

```bash
uvicorn app.main:app --reload
```

Local Swagger URL:

```text
http://127.0.0.1:8000/docs
```

## Environment variables

Create `.env` file based on `.env.example`.

Required variable:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/api_course
```

## Notes

This backend is designed for educational purposes. Some endpoints are intentionally created with incorrect behavior for bug hunting exercises.
