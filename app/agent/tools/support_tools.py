
from langchain_core.tools import tool

from app.database import SessionLocal
from app.logger import logger
from app.services.handoff_service import (
    create_support_ticket as service_create_support_ticket,
    get_support_ticket as service_get_support_ticket,
    request_human_handoff as service_request_human_handoff,
)


@tool
def create_support_ticket(
    customer_id: int,
    category: str,
    description: str,
    order_id: int | None = None,
    priority: str = "normal",
) -> dict:
    """Create a support ticket for a customer's issue.

    Use this tool when a customer reports a problem that needs follow-up,
    such as a late delivery, missing item, wrong item, or quality issue.
    """
    db = SessionLocal()

    try:
        ticket = service_create_support_ticket(
            db=db,
            customer_id=customer_id,
            category=category,
            description=description,
            order_id=order_id,
            priority=priority,
        )

        return {
            "success": True,
            "ticket_id": ticket.id,
            "customer_id": ticket.customer_id,
            "order_id": ticket.order_id,
            "category": ticket.category,
            "status": ticket.status,
            "priority": ticket.priority,
            "message": "Support ticket created successfully.",
        }

    except ValueError as exc:
        logger.warning(
            "Invalid support ticket input for customer_id=%s: %s",
            customer_id,
            str(exc),
        )
        return {"success": False, "error": str(exc)}

    except Exception:
        logger.exception(
            "Tool failed: create_support_ticket, customer_id=%s",
            customer_id,
        )
        return {
            "success": False,
            "error": "Unable to create a support ticket right now.",
        }

    finally:
        db.close()


@tool
def get_ticket_status(ticket_id: int, customer_id: int) -> dict:
    """Check the status of a support ticket belonging to a customer.

    Use this tool when a customer asks for an update on an existing ticket.
    """
    db = SessionLocal()

    try:
        ticket = service_get_support_ticket(
            db=db,
            ticket_id=ticket_id,
            customer_id=customer_id,
        )

        if ticket is None:
            return {
                "success": False,
                "error": "Support ticket not found for this customer.",
            }

        return {
            "success": True,
            "ticket_id": ticket.id,
            "order_id": ticket.order_id,
            "category": ticket.category,
            "status": ticket.status,
            "priority": ticket.priority,
            "created_at": (
                ticket.created_at.isoformat()
                if ticket.created_at
                else None
            ),
            "updated_at": (
                ticket.updated_at.isoformat()
                if ticket.updated_at
                else None
            ),
        }

    except ValueError as exc:
        logger.warning(
            "Invalid ticket lookup: ticket_id=%s, customer_id=%s: %s",
            ticket_id,
            customer_id,
            str(exc),
        )
        return {"success": False, "error": str(exc)}

    except Exception:
        logger.exception(
            "Tool failed: get_ticket_status, ticket_id=%s",
            ticket_id,
        )
        return {
            "success": False,
            "error": "Unable to retrieve ticket status right now.",
        }

    finally:
        db.close()


@tool
def request_human_handoff(
    customer_id: int,
    reason: str,
    order_id: int | None = None,
) -> dict:
    """Create a high-priority ticket requesting human support follow-up.

    Use this when a customer explicitly requests a human agent or the issue
    needs human review. This records a request; it does not connect a live
    agent automatically.
    """
    db = SessionLocal()

    try:
        ticket = service_request_human_handoff(
            db=db,
            customer_id=customer_id,
            reason=reason,
            order_id=order_id,
        )

        return {
            "success": True,
            "ticket_id": ticket.id,
            "status": ticket.status,
            "priority": ticket.priority,
            "message": (
                "Human support follow-up has been requested. "
                "A ticket has been created."
            ),
        }

    except ValueError as exc:
        logger.warning(
            "Invalid handoff request for customer_id=%s: %s",
            customer_id,
            str(exc),
        )
        return {"success": False, "error": str(exc)}

    except Exception:
        logger.exception(
            "Tool failed: request_human_handoff, customer_id=%s",
            customer_id,
        )
        return {
            "success": False,
            "error": "Unable to request human support right now.",
        }

    finally:
        db.close()


SUPPORT_TOOLS = [
    create_support_ticket,
    get_ticket_status,
    request_human_handoff,
]
