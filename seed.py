
from decimal import Decimal

from sqlalchemy.exc import SQLAlchemyError

from app.database import SessionLocal
from app.logger import logger
from app.models.customer import Customer
from app.models.order import Order, OrderItem

# Authentication import:
# This assumes hash_password is defined in app/services/auth_service.py.
from app.services.auth_service import hash_password


TEST_PASSWORD = "TestFood@123"

TEST_CUSTOMERS = [
    {
        "email": "rahul.demo@example.com",
        "orders": [
            {
                "id": 9001,
                "status": "on_the_way",
                "total": Decimal("320.00"),
                "items": [
                    ("Chicken Biryani", 2, Decimal("140.00")),
                    ("Cold Drink", 1, Decimal("40.00")),
                ],
            },
            {
                "id": 9002,
                "status": "delivered",
                "total": Decimal("450.00"),
                "items": [
                    ("Paneer Biryani", 2, Decimal("200.00")),
                    ("Lassi", 1, Decimal("50.00")),
                ],
            },
            {
                "id": 99001,
                "status": "preparing",
                "total": Decimal("220.00"),
                "items": [
                    ("Veg Biryani", 1, Decimal("180.00")),
                    ("Raita", 1, Decimal("40.00")),
                ],
            },
            {
                "id": 99002,
                "status": "on_the_way",
                "total": Decimal("459.00"),
                "items": [
                    ("Chicken Thali", 1, Decimal("299.00")),
                    ("Chocolate Brownie", 2, Decimal("80.00")),
                ],
            },
            {
                "id": 99003,
                "status": "cancelled",
                "total": Decimal("298.00"),
                "items": [
                    ("Breakfast Combo", 2, Decimal("149.00")),
                ],
            },
        ],
    },
    {
        "email": "priya.demo@example.com",
        "orders": [
            {
                "id": 9003,
                "status": "preparing",
                "total": Decimal("280.00"),
                "items": [
                    ("Veg Fried Rice", 2, Decimal("120.00")),
                    ("Fresh Lime Soda", 1, Decimal("40.00")),
                ],
            },
            {
                "id": 99004,
                "status": "delivered",
                "total": Decimal("480.00"),
                "items": [
                    ("Paneer Wrap", 2, Decimal("160.00")),
                    ("Mango Lassi", 2, Decimal("80.00")),
                ],
            },
            {
                "id": 99005,
                "status": "on_the_way",
                "total": Decimal("240.00"),
                "items": [
                    ("Masala Dosa", 1, Decimal("180.00")),
                    ("Filter Coffee", 1, Decimal("60.00")),
                ],
            },
            {
                "id": 99006,
                "status": "preparing",
                "total": Decimal("440.00"),
                "items": [
                    ("Chicken Pizza", 1, Decimal("320.00")),
                    ("Garlic Bread", 1, Decimal("120.00")),
                ],
            },
            {
                "id": 99007,
                "status": "cancelled",
                "total": Decimal("160.00"),
                "items": [
                    ("Idli", 2, Decimal("80.00")),
                ],
            },
        ],
    },
    {
        "email": "amit.demo@example.com",
        "orders": [
            {
                "id": 9004,
                "status": "cancelled",
                "total": Decimal("199.00"),
                "items": [
                    ("Masala Dosa", 1, Decimal("199.00")),
                ],
            },
            {
                "id": 99008,
                "status": "delivered",
                "total": Decimal("500.00"),
                "items": [
                    ("Butter Chicken", 1, Decimal("320.00")),
                    ("Steamed Rice", 2, Decimal("90.00")),
                ],
            },
            {
                "id": 99009,
                "status": "on_the_way",
                "total": Decimal("420.00"),
                "items": [
                    ("Veg Burger", 2, Decimal("160.00")),
                    ("French Fries", 1, Decimal("100.00")),
                ],
            },
            {
                "id": 99010,
                "status": "preparing",
                "total": Decimal("495.00"),
                "items": [
                    ("Fish Curry", 1, Decimal("390.00")),
                    ("Paratha", 3, Decimal("35.00")),
                ],
            },
            {
                "id": 99011,
                "status": "delivered",
                "total": Decimal("120.00"),
                "items": [
                    ("Samosa", 4, Decimal("30.00")),
                ],
            },
        ],
    },
]


def seed_test_data():
    db = SessionLocal()

    try:
        for customer_data in TEST_CUSTOMERS:
            email = customer_data["email"]

            customer = (
                db.query(Customer)
                .filter(Customer.email == email)
                .first()
            )

            if customer is None:
                customer = Customer(
                    email=email,
                    password_hash=hash_password(TEST_PASSWORD),
                    is_active=True,
                )
                db.add(customer)
                db.flush()

                logger.info(
                    "Created test customer: customer_id=%s",
                    customer.id,
                )
            else:
                # Keep the shared demo password stable if the account existed
                # before this seed version was added.
                customer.password_hash = hash_password(TEST_PASSWORD)
                customer.is_active = True
                logger.info(
                    "Test customer already exists: customer_id=%s",
                    customer.id,
                )

            for order_data in customer_data["orders"]:
                existing_order = (
                    db.query(Order)
                    .filter(Order.id == order_data["id"])
                    .first()
                )

                if existing_order is not None:
                    logger.info(
                        "Order already exists: order_id=%s",
                        order_data["id"],
                    )
                    continue

                order = Order(
                    id=order_data["id"],
                    customer_id=customer.id,
                    status=order_data["status"],
                    total_amount=order_data["total"],
                    items=[
                        OrderItem(
                            item_name=item_name,
                            quantity=quantity,
                            unit_price=unit_price,
                        )
                        for item_name, quantity, unit_price
                        in order_data["items"]
                    ],
                )

                db.add(order)

                logger.info(
                    "Added test order: order_id=%s, "
                    "customer_id=%s, status=%s",
                    order_data["id"],
                    customer.id,
                    order_data["status"],
                )

        db.commit()

        logger.info("Test data seeding completed successfully.")
        print("\nTest data seeded successfully.\n")
        print(f"Shared demo password: {TEST_PASSWORD}")

        for customer_data in TEST_CUSTOMERS:
            customer = (
                db.query(Customer)
                .filter(Customer.email == customer_data["email"])
                .first()
            )

            if customer is None:
                continue

            print(
                f"Email: {customer.email} | "
                f"Customer ID: {customer.id}"
            )

            for order_data in customer_data["orders"]:
                order = (
                    db.query(Order)
                    .filter(Order.id == order_data["id"])
                    .first()
                )

                if order is not None:
                    print(
                        f"  Order ID: {order.id} | "
                        f"Status: {order.status} | "
                        f"Customer ID: {order.customer_id}"
                    )

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to seed test data.")
        raise

    except Exception:
        db.rollback()
        logger.exception("Unexpected error while seeding test data.")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_test_data()
