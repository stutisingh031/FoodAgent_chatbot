
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Numeric,
    DateTime,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, nullable=False, index=True)

    status = Column(
        String(50),
        nullable=False,
        default="placed",
    )

    total_amount = Column(
        Numeric(10, 2),
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(
        Integer,
        ForeignKey("orders.id"),
        nullable=False,
        index=True,
    )

    item_name = Column(String(150), nullable=False)

    quantity = Column(Integer, nullable=False, default=1)

    unit_price = Column(Numeric(10, 2), nullable=False)

    order = relationship(
        "Order",
        back_populates="items",
    )
