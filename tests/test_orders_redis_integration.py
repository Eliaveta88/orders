import unittest
from unittest.mock import AsyncMock, patch

from src.routers.v1.orders.actions import _get_order_detail, _update_order_status
from src.routers.v1.orders.schemas import UpdateOrderStatusRequest
from src.config import redis_cfg
from src.services import redis as redis_service


class OrdersRedisIntegrationTests(unittest.IsolatedAsyncioTestCase):
    def test_redis_cfg_hardening_fields_present(self) -> None:
        self.assertGreater(redis_cfg.socket_timeout_seconds, 0)
        self.assertGreater(redis_cfg.socket_connect_timeout_seconds, 0)
        self.assertGreater(redis_cfg.health_check_interval_seconds, 0)
        self.assertGreater(redis_cfg.max_connections, 0)

    async def test_get_redis_uses_from_url_with_hardening_kwargs(self) -> None:
        redis_service._pool = None
        fake_client = AsyncMock()
        with patch(
            "src.services.redis.aioredis.from_url",
            return_value=fake_client,
        ) as from_url_mock:
            client = await redis_service.get_redis()
        self.assertIs(client, fake_client)
        from_url_mock.assert_called_once_with(
            redis_cfg.url,
            decode_responses=redis_cfg.decode_responses,
            socket_timeout=redis_cfg.socket_timeout_seconds,
            socket_connect_timeout=redis_cfg.socket_connect_timeout_seconds,
            health_check_interval=redis_cfg.health_check_interval_seconds,
            max_connections=redis_cfg.max_connections,
        )
        redis_service._pool = None

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
