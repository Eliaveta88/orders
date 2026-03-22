"""SQLAlchemy ORM models for orders service."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DECIMAL,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import mapped_column

from src.database.core import Base


class Order(Base):
    """Order database model."""

    __tablename__ = "orders"

    id: int = mapped_column(Integer, primary_key=True)
    client_id: int = mapped_column(Integer, nullable=False, index=True)
    client_name: str = mapped_column(String(255), nullable=False)
    total_amount: Decimal = mapped_column(DECIMAL(15, 2), nullable=False)
    status: str = mapped_column(
        String(50), default="draft", nullable=False, index=True
    )  # draft, confirmed, in_delivery, closed, cancelled
    delivery_date: datetime = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    route_id: int = mapped_column(Integer, nullable=True, index=True)
    notes: str = mapped_column(String(500), nullable=True)
    created_at: datetime = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: datetime = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "client_id": self.client_id,
            "client_name": self.client_name,
            "total_amount": float(self.total_amount),
            "status": self.status,
            "delivery_date": self.delivery_date,
            "route_id": self.route_id,
            "created_at": self.created_at,
        }


class OrderItem(Base):
    """Individual item in an order."""

    __tablename__ = "order_items"

    id: int = mapped_column(Integer, primary_key=True)
    order_id: int = mapped_column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: int = mapped_column(Integer, nullable=False, index=True)
    product_name: str = mapped_column(String(255), nullable=False)
    quantity: float = mapped_column(Float, nullable=False)
    unit_price: Decimal = mapped_column(DECIMAL(15, 2), nullable=False)
    total: Decimal = mapped_column(DECIMAL(15, 2), nullable=False)
    status: str = mapped_column(
        String(50), default="pending", nullable=False, index=True
    )  # pending, reserved, picked, delivered, failed
    created_at: datetime = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: datetime = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "order_id": self.order_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price),
            "total": float(self.total),
        }


class OrderStatusHistory(Base):
    """Audit log for order status changes."""

    __tablename__ = "order_status_history"

    id: int = mapped_column(Integer, primary_key=True)
    order_id: int = mapped_column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    old_status: str = mapped_column(String(50), nullable=True)
    new_status: str = mapped_column(String(50), nullable=False)
    changed_by: str = mapped_column(String(100), nullable=True)  # user_id or system
    notes: str = mapped_column(String(500), nullable=True)
    created_at: datetime = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "order_id": self.order_id,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "created_at": self.created_at,
        }
