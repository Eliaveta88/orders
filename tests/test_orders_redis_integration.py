import unittest
from unittest.mock import AsyncMock, patch

from src.routers.v1.orders.actions import _get_order_detail, _update_order_status
from src.routers.v1.orders.schemas import UpdateOrderStatusRequest


class OrdersRedisIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_order_detail_cache_hit(self) -> None:
        dal = AsyncMock()
        cached = {
            "id": 1,
            "client_id": 5,
            "client_name": "ACME",
            "items": [
                {
                    "product_id": 1,
                    "product_name": "Apple",
                    "quantity": 1,
                    "unit_price": 10.0,
                    "total": 10.0,
                }
            ],
            "total_amount": 10.0,
            "status": "confirmed",
            "delivery_date": "2030-01-01T00:00:00",
            "route_id": None,
            "created_at": "2030-01-01T00:00:00",
        }
        with patch(
            "src.routers.v1.orders.actions.get_cached_order",
            new=AsyncMock(return_value=cached),
        ):
            result = await _get_order_detail(1, dal)
        self.assertEqual(result.id, 1)
        dal.get_by_id.assert_not_called()

    async def test_update_order_status_updates_cache_and_publishes_event(self) -> None:
        dal = AsyncMock()
        dal.update_status.return_value = {
            "id": 1,
            "client_id": 5,
            "client_name": "ACME",
            "items": [
                {
                    "product_id": 1,
                    "product_name": "Apple",
                    "quantity": 1,
                    "unit_price": 10.0,
                    "total": 10.0,
                }
            ],
            "total_amount": 10.0,
            "status": "closed",
            "delivery_date": "2030-01-01T00:00:00",
            "route_id": None,
            "created_at": "2030-01-01T00:00:00",
        }
        status_req = UpdateOrderStatusRequest(status="closed")
        with (
            patch(
                "src.routers.v1.orders.actions.set_order_status",
                new=AsyncMock(),
            ) as set_mock,
            patch(
                "src.routers.v1.orders.actions.invalidate_order",
                new=AsyncMock(),
            ) as invalidate_mock,
            patch(
                "src.routers.v1.orders.actions.publish_order_event",
                new=AsyncMock(),
            ) as publish_mock,
        ):
            result = await _update_order_status(1, status_req, dal)
        self.assertEqual(result.status, "closed")
        set_mock.assert_awaited_once()
        invalidate_mock.assert_awaited_once()
        publish_mock.assert_awaited_once()
