
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.logger import logger
from app.models.order import Order


def get_recent_orders(
    db: Session,
    customer_id: int,
    limit: int = 5,
) -> list[Order]:
    """Return a customer's most recent orders."""
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")

    logger.info(
        "Fetching recent orders for customer_id=%s, limit=%s",
        customer_id,
        limit,
    )

    try:
        statement = (
            select(Order)
            .where(Order.customer_id == customer_id)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc(), Order.id.desc())
            .limit(limit)
        )

        orders = list(db.scalars(statement).all())

        logger.info(
            "Retrieved %s orders for customer_id=%s",
            len(orders),
            customer_id,
        )
        return orders

    except SQLAlchemyError:
        logger.exception(
            "Database error fetching recent orders for customer_id=%s",
            customer_id,
        )
        raise


def get_order_by_id(
    db: Session,
    customer_id: int,
    order_id: int,
) -> Order | None:
    """Find an order belonging to the specified customer."""
    logger.info(
        "Fetching order_id=%s for customer_id=%s",
        order_id,
        customer_id,
    )

    try:
        statement = (
            select(Order)
            .where(
                Order.id == order_id,
                Order.customer_id == customer_id,
            )
            .options(selectinload(Order.items))
        )

        order = db.scalar(statement)

        if order is None:
            logger.warning(
                "Order not found or not accessible: order_id=%s, customer_id=%s",
                order_id,
                customer_id,
            )
        else:
            logger.info("Order retrieved successfully: order_id=%s", order_id)

        return order

    except SQLAlchemyError:
        logger.exception(
            "Database error fetching order_id=%s for customer_id=%s",
            order_id,
            customer_id,
        )
        raise


def get_order_items(
    db: Session,
    customer_id: int,
    order_id: int,
) -> list[dict]:
    """Return items only when the order belongs to the customer."""
    order = get_order_by_id(db, customer_id, order_id)

    if order is None:
        return []

    return [
        {
            "item_name": item.item_name,
            "quantity": item.quantity,
            "unit_price": float(item.unit_price),
        }
        for item in order.items
    ]


def get_delivery_status(
    db: Session,
    customer_id: int,
    order_id: int,
) -> str | None:
    """Return the status of a customer's order."""
    order = get_order_by_id(db, customer_id, order_id)

    if order is None:
        return None

    return order.status
