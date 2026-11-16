
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.logger import logger
from app.services.order_service import (
    get_recent_orders as fetch_recent_orders,
)

# Create the orders router
router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


# Define the API response structure
class OrderResponse(BaseModel):
    id: int
    customer_id: int
    status: str
    total_amount: float


# GET /orders/recent
@router.get("/recent", response_model=list[OrderResponse])
def recent_orders(
    customer_id: int = Query(..., gt=0),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Retrieve recent orders for a customer.

    Args:
        customer_id: ID of the customer.
        limit: Maximum number of orders to return.
        db: Database session.

    Returns:
        A list of recent orders.
    """
    logger.info(
        "Recent orders requested: customer_id=%s, limit=%s",
        customer_id,
        limit,
    )

    try:
        orders = fetch_recent_orders(
            db=db,
            customer_id=customer_id,
            limit=limit,
        )

        response = [
            OrderResponse(
                id=order.id,
                customer_id=order.customer_id,
                status=order.status,
                total_amount=float(order.total_amount),
            )
            for order in orders
        ]

        logger.info(
            "Retrieved %s orders for customer_id=%s",
            len(response),
            customer_id,
        )

        return response

    except SQLAlchemyError:
        logger.exception(
            "Database error retrieving orders for customer_id=%s",
            customer_id,
        )
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve orders right now.",
        ) from None

    except Exception:
        logger.exception(
            "Unexpected error retrieving orders for customer_id=%s",
            customer_id,
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving orders.",
        ) from None
