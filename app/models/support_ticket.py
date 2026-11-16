
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from app.database import Base


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, nullable=False, index=True)
    order_id = Column(Integer, nullable=True, index=True)

    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)

    status = Column(
        String(30),
        nullable=False,
        default="open",
        server_default="open",
    )

    priority = Column(
        String(20),
        nullable=False,
        default="normal",
        server_default="normal",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
