
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.conversation import Conversation
from app.logger import logger


def save_message(
    db: Session,
    customer_id: int,
    session_id: str,
    role: str,
    message: str,
) -> Conversation:
    """Save one customer or assistant message to the database."""

    if customer_id <= 0:
        raise ValueError("customer_id must be positive.")

    if not session_id or not session_id.strip():
        raise ValueError("session_id cannot be empty.")

    if role not in {"user", "assistant"}:
        raise ValueError("role must be 'user' or 'assistant'.")

    if not message or not message.strip():
        raise ValueError("message cannot be empty.")

    conversation = Conversation(
        customer_id=customer_id,
        session_id=session_id.strip(),
        role=role,
        message=message.strip(),
    )

    try:
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        logger.info(
            "Conversation message saved: customer_id=%s, session_id=%s, role=%s",
            customer_id,
            session_id,
            role,
        )
        return conversation

    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Failed to save conversation message for customer_id=%s",
            customer_id,
        )
        raise


def get_conversation_history(
    db: Session,
    customer_id: int,
    session_id: str,
    limit: int = 20,
) -> list[Conversation]:
    """Retrieve the latest messages from one customer session."""

    if customer_id <= 0:
        raise ValueError("customer_id must be positive.")

    if not session_id or not session_id.strip():
        raise ValueError("session_id cannot be empty.")

    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100.")

    try:
        messages = (
            db.query(Conversation)
            .filter(
                Conversation.customer_id == customer_id,
                Conversation.session_id == session_id.strip(),
            )
            .order_by(Conversation.created_at.desc(), Conversation.id.desc())
            .limit(limit)
            .all()
        )

        # Return messages in chronological order.
        messages.reverse()

        logger.info(
            "Conversation history retrieved: customer_id=%s, session_id=%s, count=%s",
            customer_id,
            session_id,
            len(messages),
        )
        return messages

    except SQLAlchemyError:
        logger.exception(
            "Failed to retrieve conversation history for customer_id=%s",
            customer_id,
        )
        raise


def get_latest_session_id(
    db: Session,
    customer_id: int,
) -> str | None:
    """Return the session containing a customer's most recent message."""

    if customer_id <= 0:
        raise ValueError("customer_id must be positive.")

    try:
        latest = (
            db.query(Conversation.session_id)
            .filter(Conversation.customer_id == customer_id)
            .order_by(Conversation.created_at.desc(), Conversation.id.desc())
            .first()
        )
        return latest[0] if latest else None
    except SQLAlchemyError:
        logger.exception(
            "Failed to retrieve latest conversation session for customer_id=%s",
            customer_id,
        )
        raise
