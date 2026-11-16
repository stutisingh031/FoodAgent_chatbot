
from langchain_core.tools import tool

from app.database import SessionLocal
from app.logger import logger
from app.services.order_service import (
    get_recent_orders as service_get_recent_orders,
    get_order_by_id,
    get_order_items as service_get_order_items,
    get_delivery_status as service_get_delivery_status,
)


@tool
def get_recent_orders(customer_id: int) -> dict:
    """Get the five most recent orders for a customer.

    Use this tool when a customer asks about their recent or previous orders.
    """
    db = SessionLocal()

    try:
        orders = service_get_recent_orders(db, customer_id, limit=5)

        return {
            "customer_id": customer_id,
            "orders": [
                {
                    "order_id": order.id,
                    "status": order.status,
                    "total_amount": float(order.total_amount),
                    "created_at": (
                        order.created_at.isoformat()
                        if order.created_at
                        else None
                    ),
                }
                for order in orders
            ],
        }

    except Exception:
        logger.exception(
            "Tool failed: get_recent_orders, customer_id=%s",
            customer_id,
        )
        return {"error": "Unable to retrieve recent orders right now."}

    finally:
        db.close()


@tool
def get_order_details(customer_id: int, order_id: int) -> dict:
    """Get details of an order belonging to a customer.

    Use this tool when a customer asks about a specific order.
    """
    db = SessionLocal()

    try:
        order = get_order_by_id(db, customer_id, order_id)

        if order is None:
            return {"error": "Order not found for this customer."}

        return {
            "order_id": order.id,
            "status": order.status,
            "total_amount": float(order.total_amount),
            "created_at": (
                order.created_at.isoformat()
                if order.created_at
                else None
            ),
            "items": [
                {
                    "item_name": item.item_name,
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price),
                }
                for item in order.items
            ],
        }

    except Exception:
        logger.exception(
            "Tool failed: get_order_details, customer_id=%s, order_id=%s",
            customer_id,
            order_id,
        )
        return {"error": "Unable to retrieve order details right now."}

    finally:
        db.close()


@tool
def get_order_items(customer_id: int, order_id: int) -> dict:
    """Get the food items in an order belonging to a customer."""
    db = SessionLocal()

    try:
        items = service_get_order_items(db, customer_id, order_id)

        if not items:
            order = get_order_by_id(db, customer_id, order_id)
            if order is None:
                return {"error": "Order not found for this customer."}

        return {"order_id": order_id, "items": items}

    except Exception:
        logger.exception(
            "Tool failed: get_order_items, customer_id=%s, order_id=%s",
            customer_id,
            order_id,
        )
        return {"error": "Unable to retrieve order items right now."}

    finally:
        db.close()


@tool
def get_delivery_status(customer_id: int, order_id: int) -> dict:
    """Check the delivery status of an order belonging to a customer."""
    db = SessionLocal()

    try:
        status = service_get_delivery_status(db, customer_id, order_id)

        if status is None:
            return {"error": "Order not found for this customer."}

        return {"order_id": order_id, "status": status}

    except Exception:
        logger.exception(
            "Tool failed: get_delivery_status, customer_id=%s, order_id=%s",
            customer_id,
            order_id,
        )
        return {"error": "Unable to retrieve delivery status right now."}

    finally:
        db.close()


ORDER_TOOLS = [
    get_recent_orders,
    get_order_details,
    get_order_items,
    get_delivery_status,
]
