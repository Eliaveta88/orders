"""OrderListResponse и фильтры списка — контракт KPI / пагинация (план P2)."""

import unittest
from datetime import datetime, timezone

from src.routers.v1.orders.schemas import OrderListResponse, OrderSummaryResponse


class TestOrderListResponse(unittest.TestCase):
    def test_parse_list_payload(self) -> None:
        now = datetime.now(timezone.utc)
        data = {
            "items": [
                {
                    "id": 1,
                    "client_id": 10,
                    "client_name": "Client",
                    "total_amount": 100.0,
                    "status": "draft",
                    "delivery_date": now,
                    "route_id": None,
                    "created_at": now,
                },
            ],
            "total": 99,
            "skip": 0,
            "limit": 50,
        }
        m = OrderListResponse.model_validate(data)
        self.assertEqual(m.total, 99)
        self.assertEqual(len(m.items), 1)
        self.assertIsInstance(m.items[0], OrderSummaryResponse)


if __name__ == "__main__":
    unittest.main()
