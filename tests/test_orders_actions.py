"""Unit tests for order actions (mocks for catalog/identity HTTP; no real network)."""

from __future__ import annotations

import unittest
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

import src.routers.v1.orders.actions as orders_actions
from src.routers.v1.orders.actions import _create_order
from src.routers.v1.orders.schemas import CreateOrderItemRequest, CreateOrderRequest


class OrdersActionsTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_order_passes_resolved_lines_and_identity_client_name(self) -> None:
        dal = AsyncMock()
        created = datetime(2030, 1, 1, tzinfo=UTC)
        dal.create.return_value = {
            "id": 42,
            "client_id": 1,
            "client_name": "alice",
            "items": [
                {
                    "product_id": 10,
                    "product_name": "Item A",
                    "quantity": 2.0,
                    "unit_price": 99.5,
                    "total": 199.0,
                }
            ],
            "total_amount": 199.0,
            "status": "draft",
            "delivery_date": created,
            "route_id": None,
            "created_at": created,
        }
        req = CreateOrderRequest(
            client_id=1,
            items=[CreateOrderItemRequest(product_id=10, quantity=2.0)],
            delivery_date=created,
        )
        with (
            patch.object(
                orders_actions,
                "fetch_product",
                new=AsyncMock(return_value={"name": "Item A", "price": 99.5}),
            ),
            patch.object(
                orders_actions,
                "fetch_user_display_name",
                new=AsyncMock(return_value="alice"),
            ),
            patch.object(orders_actions, "cache_order", new=AsyncMock()),
            patch.object(orders_actions, "set_order_status", new=AsyncMock()),
            patch.object(orders_actions, "publish_order_event", new=AsyncMock()),
        ):
            result = await _create_order(req, dal)

        self.assertEqual(result.id, 42)
        self.assertEqual(result.client_name, "alice")
        dal.create.assert_awaited_once()
        kwargs = dal.create.await_args.kwargs
        self.assertEqual(kwargs["client_name"], "alice")
        lines = kwargs["resolved_lines"]
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0][0], Decimal("99.5"))
        self.assertEqual(lines[0][1], "Item A")

    async def test_create_order_fallback_client_name_when_identity_returns_none(self) -> None:
        dal = AsyncMock()
        created = datetime(2030, 1, 1, tzinfo=UTC)
        dal.create.return_value = {
            "id": 1,
            "client_id": 7,
            "client_name": "Client #7",
            "items": [
                {
                    "product_id": 1,
                    "product_name": "P",
                    "quantity": 1.0,
                    "unit_price": 1.0,
                    "total": 1.0,
                }
            ],
            "total_amount": 1.0,
            "status": "draft",
            "delivery_date": created,
            "route_id": None,
            "created_at": created,
        }
        req = CreateOrderRequest(
            client_id=7,
            items=[CreateOrderItemRequest(product_id=1, quantity=1.0)],
            delivery_date=created,
        )
        with (
            patch.object(
                orders_actions,
                "fetch_product",
                new=AsyncMock(return_value={"name": "P", "price": 1}),
            ),
            patch.object(
                orders_actions,
                "fetch_user_display_name",
                new=AsyncMock(return_value=None),
            ),
            patch.object(orders_actions, "cache_order", new=AsyncMock()),
            patch.object(orders_actions, "set_order_status", new=AsyncMock()),
            patch.object(orders_actions, "publish_order_event", new=AsyncMock()),
        ):
            await _create_order(req, dal)

        kwargs = dal.create.await_args.kwargs
        self.assertEqual(kwargs["client_name"], "Client #7")

    async def test_create_order_product_not_found_returns_400(self) -> None:
        dal = AsyncMock()
        created = datetime(2030, 1, 1, tzinfo=UTC)
        req = CreateOrderRequest(
            client_id=1,
            items=[CreateOrderItemRequest(product_id=999, quantity=1.0)],
            delivery_date=created,
        )
        with (
            patch.object(
                orders_actions,
                "fetch_product",
                new=AsyncMock(return_value=None),
            ),
            patch.object(
                orders_actions,
                "fetch_user_display_name",
                new=AsyncMock(return_value="u"),
            ),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await _create_order(req, dal)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("not found", str(ctx.exception.detail).lower())
        dal.create.assert_not_awaited()
