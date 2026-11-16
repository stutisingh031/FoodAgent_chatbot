
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.agent.support_agent import chat_with_support_agent
from app.database import get_db
from app.logger import logger
from app.services.conversation_service import (
    save_message,
    get_conversation_history,
    get_latest_session_id,
)

router = APIRouter(prefix="/chat", tags=["Chat"])


# --------------------------------------------------
# Chatbot welcome message and quick-reply options
# --------------------------------------------------

CHATBOT_WELCOME = {
    "welcome_message": (
        "Hi! Welcome to Food Support! 👋 "
        "How can I help you today?"
    ),
    "options": [
        {
            "id": "track_order",
            "label": "Track my order",
        },
        {
            "id": "order_issue",
            "label": "Order issue",
        },
        {
            "id": "payment_issue",
            "label": "Payment issue",
        },
        {
            "id": "missing_item",
            "label": "Missing or incorrect items",
        },
        {
            "id": "cancel_order",
            "label": "Cancel my order",
        },
    ],
}


@router.get("/options")
def get_chatbot_options():
    """Return the welcome message and chatbot quick-reply options."""

    logger.info("Chatbot welcome options requested")

    return CHATBOT_WELCOME


# --------------------------------------------------
# Request and response models
# --------------------------------------------------

class ChatRequest(BaseModel):
    customer_id: int = Field(gt=0)
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    handoff_required: bool = False
    ticket_id: int | None = None


class ConversationMessageResponse(BaseModel):
    id: int
    role: str
    message: str
    created_at: datetime


# --------------------------------------------------
# Send a message to the AI support agent
# --------------------------------------------------

@router.post("", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:

    message = request.message.strip()

    if not message:
        raise HTTPException(
            status_code=422,
            detail="Message cannot be empty.",
        )

    session_id = (
        request.session_id.strip()
        if request.session_id
        else str(uuid4())
    )

    if not session_id:
        raise HTTPException(
            status_code=422,
            detail="Session ID cannot be empty.",
        )

    logger.info(
        "Chat request received: customer_id=%s, session_id=%s",
        request.customer_id,
        session_id,
    )

    try:
        # 1. Save the current customer message.
        save_message(
            db=db,
            customer_id=request.customer_id,
            session_id=session_id,
            role="user",
            message=message,
        )

        # 2. Retrieve recent conversation history.
        history = get_conversation_history(
            db=db,
            customer_id=request.customer_id,
            session_id=session_id,
            limit=21,
        )

        # 3. Exclude the current message so the agent
        #    does not receive it twice.
        previous_history = [
            item
            for item in history
            if item.role in {"user", "assistant"}
            and item.id is not None
            and not (
                item.role == "user"
                and item.message == message
            )
        ]

        # 4. Keep recent messages in chronological order.
        history_for_agent = [
            {
                "role": item.role,
                "message": item.message,
            }
            for item in previous_history[-20:]
        ]

        # 5. Ask the AI agent to resolve the issue and return any
        #    structured human-ticket decision made by its support tools.
        agent_response = chat_with_support_agent(
            message=message,
            customer_id=request.customer_id,
            history=history_for_agent,
        )

        # 6. Save the AI response.
        save_message(
            db=db,
            customer_id=request.customer_id,
            session_id=session_id,
            role="assistant",
            message=agent_response.reply,
        )

        logger.info(
            "Chat response completed: customer_id=%s, session_id=%s, handoff_required=%s, ticket_id=%s",
            request.customer_id,
            session_id,
            agent_response.handoff_required,
            agent_response.ticket_id,
        )

        return ChatResponse(
            reply=agent_response.reply,
            session_id=session_id,
            handoff_required=agent_response.handoff_required,
            ticket_id=agent_response.ticket_id,
        )

    except ValueError:
        logger.warning(
            "Invalid chat request: customer_id=%s",
            request.customer_id,
        )

        raise HTTPException(
            status_code=422,
            detail="Invalid chat request.",
        ) from None

    except SQLAlchemyError:
        logger.exception(
            "Database error during chat: customer_id=%s, session_id=%s",
            request.customer_id,
            session_id,
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to save or retrieve conversation history.",
        ) from None

    except Exception:
        logger.exception(
            "Chat request failed: customer_id=%s, session_id=%s",
            request.customer_id,
            session_id,
        )

        raise HTTPException(
            status_code=500,
            detail="The support service is temporarily unavailable.",
        ) from None


# --------------------------------------------------
# Retrieve conversation history
# --------------------------------------------------

@router.get("/latest-session")
def latest_conversation_session(
    customer_id: int,
    db: Session = Depends(get_db),
) -> dict[str, str | None]:
    """Return the latest saved chat session for a customer."""

    if customer_id <= 0:
        raise HTTPException(
            status_code=422,
            detail="customer_id must be positive.",
        )

    try:
        return {"session_id": get_latest_session_id(db, customer_id)}
    except SQLAlchemyError:
        logger.exception(
            "Failed to retrieve latest conversation session: customer_id=%s",
            customer_id,
        )
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve conversation history.",
        ) from None

@router.get(
    "/{session_id}/history",
    response_model=list[ConversationMessageResponse],
)
def conversation_history(
    session_id: str,
    customer_id: int,
    db: Session = Depends(get_db),
) -> list[ConversationMessageResponse]:
    """Return messages belonging to a customer's chat session."""

    if customer_id <= 0:
        raise HTTPException(
            status_code=422,
            detail="customer_id must be positive.",
        )

    if not session_id.strip():
        raise HTTPException(
            status_code=422,
            detail="session_id cannot be empty.",
        )

    logger.info(
        "Conversation history requested: customer_id=%s, session_id=%s",
        customer_id,
        session_id,
    )

    try:
        history = get_conversation_history(
            db=db,
            customer_id=customer_id,
            session_id=session_id,
            limit=100,
        )

        return [
            ConversationMessageResponse(
                id=item.id,
                role=item.role,
                message=item.message,
                created_at=item.created_at,
            )
            for item in history
        ]

    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Invalid conversation history request.",
        ) from None

    except SQLAlchemyError:
        logger.exception(
            "Failed to retrieve conversation history: customer_id=%s, session_id=%s",
            customer_id,
            session_id,
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve conversation history.",
        ) from None
