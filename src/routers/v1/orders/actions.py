"""Orders business logic."""

from src.routers.v1.orders.dal import OrderDAL


class OrderActions:
    def __init__(self, dal: OrderDAL):
        self.dal = dal

    async def create_order(self, data: dict) -> dict:
        return await self.dal.create(data)

    async def list_orders(self, skip: int = 0, limit: int = 100) -> list[dict]:
        return await self.dal.get_all(skip, limit)
