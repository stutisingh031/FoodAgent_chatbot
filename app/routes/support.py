
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.logger import logger
from pydantic import BaseModel, Field, field_validator
from app.services.handoff_service import (
    create_support_ticket as create_ticket_service,
    get_support_ticket as get_ticket_service,
)
ALLOWED_CATEGORIES = {
    "late_delivery",
    "missing_item",
    "wrong_item",
    "order_status",
    "quality_issue",
    "cancellation",
    "refund_query",
    "general_support",
}

ALLOWED_PRIORITIES = {"low", "normal", "high"}

router = APIRouter(prefix="/support", tags=["Support"])


# Request model for creating a ticket
class TicketCreateRequest(BaseModel):
    customer_id: int = Field(gt=0)
    category: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=5, max_length=3000)
    order_id: int | None = Field(default=None, gt=0)
    priority: str = Field(default="normal", pattern="^(low|normal|high)$")

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        value = value.strip().lower()
        if value not in ALLOWED_CATEGORIES:
            raise ValueError("Unsupported support category.")
        return value

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str) -> str:
        value = value.strip().lower()
        if value not in ALLOWED_PRIORITIES:
            raise ValueError("Unsupported priority level.")
        return value


# Response model
class TicketResponse(BaseModel):
    id: int
    customer_id: int
    order_id: int | None
    category: str
    description: str
    status: str
    priority: str


# POST /support/tickets
@router.post("/tickets", response_model=TicketResponse, status_code=201)
def create_ticket(
    request: TicketCreateRequest,
    db: Session = Depends(get_db),
):
    logger.info(
        "Ticket creation requested for customer_id=%s, category=%s",
        request.customer_id,
        request.category,
    )

    try:
        ticket = create_ticket_service(
            db=db,
            customer_id=request.customer_id,
            category=request.category,
            description=request.description,
            order_id=request.order_id,
            priority=request.priority,
        )

        logger.info("Support ticket created: ticket_id=%s", ticket.id)

        return TicketResponse(
            id=ticket.id,
            customer_id=ticket.customer_id,
            order_id=ticket.order_id,
            category=ticket.category,
            description=ticket.description,
            status=ticket.status,
            priority=ticket.priority,
        )

    except ValueError as exc:
        logger.warning("Invalid ticket request: %s", str(exc))
        raise HTTPException(
            status_code=422,
            detail="Invalid support ticket details.",
        ) from None

    except SQLAlchemyError:
        logger.exception("Database error while creating support ticket")
        raise HTTPException(
            status_code=500,
            detail="Unable to create a support ticket right now.",
        ) from None

    except Exception:
        logger.exception("Unexpected error while creating support ticket")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred.",
        ) from None


# GET /support/tickets/{ticket_id}
@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: int,
    customer_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    logger.info(
        "Ticket lookup requested: ticket_id=%s, customer_id=%s",
        ticket_id,
        customer_id,
    )

    try:
        ticket = get_ticket_service(
            db=db,
            ticket_id=ticket_id,
            customer_id=customer_id,
        )

        if ticket is None:
            raise HTTPException(
                status_code=404,
                detail="Support ticket not found.",
            )

        return TicketResponse(
            id=ticket.id,
            customer_id=ticket.customer_id,
            order_id=ticket.order_id,
            category=ticket.category,
            description=ticket.description,
            status=ticket.status,
            priority=ticket.priority,
        )

    except HTTPException:
        raise

    except SQLAlchemyError:
        logger.exception(
            "Database error retrieving ticket_id=%s",
            ticket_id,
        )
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve the support ticket right now.",
        ) from None

    except Exception:
        logger.exception(
            "Unexpected error retrieving ticket_id=%s",
            ticket_id,
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred.",
        ) from None
