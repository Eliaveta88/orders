"""Orders DAL."""

from sqlalchemy.ext.asyncio import AsyncSession


class OrderDAL:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict) -> dict:
        return {"id": 1, **data}

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[dict]:
        return []
