"""Data Access Layer for orders operations."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.routers.v1.orders.models import Order, OrderItem, OrderStatusHistory
from src.routers.v1.orders.schemas import CreateOrderRequest


class OrderDAL:
    """Data Access Layer for order management."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_orders(
        self,
        skip: int = 0,
        limit: int = 100,
        *,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> list[dict]:
        """List orders with pagination and optional created_at range (half-open [from, to))."""
        stmt = select(Order).order_by(Order.created_at.desc())
        if created_from is not None:
            stmt = stmt.where(Order.created_at >= created_from)
        if created_to is not None:
            stmt = stmt.where(Order.created_at < created_to)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        orders = result.scalars().all()
        return [o.to_dict() | {"id": o.id} for o in orders]

    async def count_orders(
        self,
        *,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> int:
        """Count orders, optionally filtered by created_at range (half-open [from, to))."""
        stmt = select(func.count(Order.id))
        if created_from is not None:
            stmt = stmt.where(Order.created_at >= created_from)
        if created_to is not None:
            stmt = stmt.where(Order.created_at < created_to)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_by_id(self, order_id: int) -> dict | None:
        """Get order by ID."""
        stmt = select(Order).where(Order.id == order_id)
        result = await self.session.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            return None

        # 1. Get order items
        items_stmt = select(OrderItem).where(OrderItem.order_id == order_id)
        items_result = await self.session.execute(items_stmt)
        items = items_result.scalars().all()

        # 2. Build response
        return {
            "id": order.id,
            "client_id": order.client_id,
            "client_name": order.client_name,
            "items": [
                {
                    "product_id": item.product_id,
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price),
                    "total": float(item.total),
                }
                for item in items
            ],
            "total_amount": float(order.total_amount),
            "status": order.status,
            "delivery_date": order.delivery_date,
            "route_id": order.route_id,
            "created_at": order.created_at,
        }

    async def create(self, order_in: CreateOrderRequest) -> dict:
        """Create new order."""
        # 1. Calculate total amount
        total_amount = Decimal("0")
        items_data = []

        for item in order_in.items:
            # TODO: Fetch product price from catalog service
            unit_price = Decimal("100")  # Mock price
            item_total = Decimal(item.quantity) * unit_price
            total_amount += item_total
            items_data.append((item, unit_price, item_total))

        # 2. Create Order record
        order = Order(
            client_id=order_in.client_id,
            client_name="Client Name",  # TODO: Fetch from clients
            total_amount=total_amount,
            status="draft",
            delivery_date=order_in.delivery_date,
            notes=order_in.notes,
        )
        self.session.add(order)
        await self.session.flush()

        # 3. Create OrderItem records for each item
        for item_req, unit_price, item_total in items_data:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_req.product_id,
                product_name="Product Name",  # TODO: Fetch from catalog
                quantity=item_req.quantity,
                unit_price=unit_price,
                total=item_total,
                status="pending",
            )
            self.session.add(order_item)

        await self.session.flush()

        # 4. Return order details
        return {
            "id": order.id,
            "client_id": order.client_id,
            "client_name": order.client_name,
            "items": [
                {
                    "product_id": item.product_id,
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": float(unit_price),
                    "total": float(item_total),
                }
                for item, unit_price, item_total in items_data
            ],
            "total_amount": float(total_amount),
            "status": "draft",
            "delivery_date": order.delivery_date,
            "route_id": None,
            "created_at": order.created_at,
        }

    async def update_status(self, order_id: int, new_status: str) -> dict | None:
        """Update order status."""
        # 1. Find order
        stmt = select(Order).where(Order.id == order_id)
        result = await self.session.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            return None

        # 2. Record status change in history
        history = OrderStatusHistory(
            order_id=order_id,
            old_status=order.status,
            new_status=new_status,
            changed_by="system",
        )
        self.session.add(history)

        # 3. Update status
        await self.session.execute(
            update(Order).where(Order.id == order_id).values(status=new_status)
        )
        await self.session.flush()

        # 4. Return updated order
        return await self.get_by_id(order_id)
