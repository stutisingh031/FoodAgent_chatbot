
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.logger import logger
from app.models.support_ticket import SupportTicket


def create_support_ticket(
    db: Session,
    customer_id: int,
    category: str,
    description: str,
    order_id: int | None = None,
    priority: str = "normal",
) -> SupportTicket:
    """Create a support ticket for a customer issue."""

    category = category.strip()
    description = description.strip()
    priority = priority.strip().lower()

    if customer_id <= 0:
        raise ValueError("customer_id must be positive")

    if not category:
        raise ValueError("category cannot be empty")

    if not description:
        raise ValueError("description cannot be empty")

    if order_id is not None and order_id <= 0:
        raise ValueError("order_id must be positive")

    if priority not in {"low", "normal", "high", "urgent"}:
        raise ValueError("priority must be low, normal, high, or urgent")

    ticket = SupportTicket(
        customer_id=customer_id,
        order_id=order_id,
        category=category,
        description=description,
        priority=priority,
        status="open",
    )

    try:
        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        logger.info(
            "Support ticket created: ticket_id=%s, customer_id=%s, category=%s",
            ticket.id,
            customer_id,
            category,
        )
        return ticket

    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database error creating support ticket for customer_id=%s",
            customer_id,
        )
        raise


def get_support_ticket(
    db: Session,
    ticket_id: int,
    customer_id: int,
) -> SupportTicket | None:
    """Retrieve a ticket only if it belongs to the specified customer."""

    if ticket_id <= 0 or customer_id <= 0:
        raise ValueError("ticket_id and customer_id must be positive")

    logger.info(
        "Looking up support ticket: ticket_id=%s, customer_id=%s",
        ticket_id,
        customer_id,
    )

    try:
        ticket = (
            db.query(SupportTicket)
            .filter(
                SupportTicket.id == ticket_id,
                SupportTicket.customer_id == customer_id,
            )
            .first()
        )

        if ticket is None:
            logger.warning(
                "Support ticket not found or inaccessible: "
                "ticket_id=%s, customer_id=%s",
                ticket_id,
                customer_id,
            )

        return ticket

    except SQLAlchemyError:
        logger.exception(
            "Database error retrieving ticket_id=%s for customer_id=%s",
            ticket_id,
            customer_id,
        )
        raise


def request_human_handoff(
    db: Session,
    customer_id: int,
    reason: str,
    order_id: int | None = None,
) -> SupportTicket:
    """Create a ticket requesting follow-up by a human agent."""

    reason = reason.strip()

    if not reason:
        raise ValueError("A handoff reason is required")

    logger.info(
        "Human handoff requested: customer_id=%s, order_id=%s",
        customer_id,
        order_id,
    )

    return create_support_ticket(
        db=db,
        customer_id=customer_id,
        order_id=order_id,
        category="human_handoff",
        description=reason,
        priority="high",
    )
