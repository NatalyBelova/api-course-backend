from decimal import Decimal

from app.database import SessionLocal
from app.models.models import Category, Product


def seed_data() -> None:
    db = SessionLocal()

    try:
        existing_categories = db.query(Category).count()
        existing_products = db.query(Product).count()

        if existing_categories > 0 or existing_products > 0:
            print("Seed data already exists. Skipping.")
            return

        categories = [
            Category(
                name="Electronics",
                slug="electronics",
                description="Electronic devices and accessories",
            ),
            Category(
                name="Clothes",
                slug="clothes",
                description="Clothes and everyday wear",
            ),
            Category(
                name="Books",
                slug="books",
                description="Books and learning materials",
            ),
            Category(
                name="Home",
                slug="home",
                description="Home appliances and household goods",
            ),
            Category(
                name="Beauty",
                slug="beauty",
                description="Beauty and personal care products",
            ),
            Category(
                name="Sport",
                slug="sport",
                description="Sport and outdoor products",
            ),
        ]

        db.add_all(categories)
        db.commit()

        category_by_slug = {
            category.slug: category
            for category in db.query(Category).all()
        }

        products = [
            Product(
                category_id=category_by_slug["electronics"].id,
                name="Wireless Headphones",
                description="Bluetooth wireless headphones",
                price=Decimal("99.99"),
                stock=15,
                rating=Decimal("4.7"),
                is_active=True,
            ),
            Product(
                category_id=category_by_slug["electronics"].id,
                name="Gaming Keyboard",
                description="Mechanical gaming keyboard with RGB backlight",
                price=Decimal("120.00"),
                stock=8,
                rating=Decimal("4.5"),
                is_active=True,
            ),
            Product(
                category_id=category_by_slug["electronics"].id,
                name="Smartphone Case",
                description="Protective smartphone case",
                price=Decimal("15.50"),
                stock=50,
                rating=Decimal("4.2"),
                is_active=True,
            ),
            Product(
                category_id=category_by_slug["clothes"].id,
                name="Cotton Hoodie",
                description="Soft cotton hoodie",
                price=Decimal("45.50"),
                stock=20,
                rating=Decimal("4.4"),
                is_active=True,
            ),
            Product(
                category_id=category_by_slug["sport"].id,
                name="Running Shoes",
                description="Lightweight running shoes",
                price=Decimal("89.90"),
                stock=10,
                rating=Decimal("4.6"),
                is_active=True,
            ),
            Product(
                category_id=category_by_slug["books"].id,
                name="QA Testing Book",
                description="Practical book for QA engineers",
                price=Decimal("30.00"),
                stock=12,
                rating=Decimal("4.9"),
                is_active=True,
            ),
            Product(
                category_id=category_by_slug["home"].id,
                name="Coffee Machine",
                description="Automatic coffee machine for home use",
                price=Decimal("250.00"),
                stock=5,
                rating=Decimal("4.3"),
                is_active=True,
            ),
            Product(
                category_id=category_by_slug["beauty"].id,
                name="Face Cream",
                description="Moisturizing face cream",
                price=Decimal("18.90"),
                stock=30,
                rating=Decimal("4.1"),
                is_active=True,
            ),
            Product(
                category_id=category_by_slug["electronics"].id,
                name="Out of Stock Laptop",
                description="Laptop used for testing out-of-stock scenarios",
                price=Decimal("999.00"),
                stock=0,
                rating=Decimal("4.8"),
                is_active=True,
            ),
            Product(
                category_id=category_by_slug["home"].id,
                name="Inactive Product",
                description="Product used for testing inactive product scenarios",
                price=Decimal("10.00"),
                stock=10,
                rating=Decimal("3.5"),
                is_active=False,
            ),
        ]

        db.add_all(products)
        db.commit()

        print("Seed data created successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_data()