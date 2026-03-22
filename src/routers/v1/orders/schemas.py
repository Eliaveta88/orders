"""Orders schemas and models."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class OrderItem(BaseModel):
    """Single item in order."""

    product_id: int = Field(..., gt=0, description="Product ID")
    product_name: str = Field(..., description="Product name")
    quantity: float = Field(..., gt=0, description="Quantity ordered")
    unit_price: float = Field(..., ge=0, description="Price per unit")
    total: float = Field(..., ge=0, description="Total (qty * price)")


class OrderSummaryResponse(BaseModel):
    """Краткая карточка заказа для списка (без позиций)."""

    id: int = Field(..., description="Order ID")
    client_id: int = Field(..., description="Client ID")
    client_name: str = Field(..., description="Client name")
    total_amount: float = Field(..., ge=0, description="Total order amount")
    status: str = Field(
        ..., description="Order status: draft, confirmed, in_delivery, closed, cancelled"
    )
    delivery_date: datetime = Field(..., description="Delivery date")
    route_id: Optional[int] = Field(None, description="Assigned route ID")
    created_at: datetime = Field(..., description="Creation timestamp")


class OrderResponse(BaseModel):
    """Order response."""

    id: int = Field(..., description="Order ID")
    client_id: int = Field(..., description="Client ID")
    client_name: str = Field(..., description="Client name")
    items: List[OrderItem] = Field(..., min_items=1, description="Order items")
    total_amount: float = Field(..., ge=0, description="Total order amount")
    status: str = Field(
        ..., description="Order status: draft, confirmed, in_delivery, closed, cancelled"
    )
    delivery_date: datetime = Field(..., description="Delivery date")
    route_id: Optional[int] = Field(None, description="Assigned route ID")
    created_at: datetime = Field(..., description="Creation timestamp")


class OrderListResponse(BaseModel):
    """Paginated list of orders."""

    items: List[OrderSummaryResponse]
    total: int = Field(..., ge=0, description="Total orders count")
    skip: int = Field(..., ge=0, description="Pagination offset")
    limit: int = Field(..., ge=1, le=100, description="Pagination limit")


class CreateOrderItemRequest(BaseModel):
    """Item to add to order."""

    product_id: int = Field(..., gt=0, description="Product ID")
    quantity: float = Field(..., gt=0, description="Quantity")


class CreateOrderRequest(BaseModel):
    """Request to create order."""

    client_id: int = Field(..., gt=0, description="Client ID")
    items: List[CreateOrderItemRequest] = Field(..., min_items=1, description="Order items")
    delivery_date: datetime = Field(..., description="Desired delivery date")
    notes: Optional[str] = Field(None, max_length=500, description="Special instructions")


class UpdateOrderStatusRequest(BaseModel):
    """Request to update order status."""

    status: str = Field(..., description="New status: confirmed, in_delivery, closed, cancelled")
