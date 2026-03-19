import os
from abc import ABC
from dataclasses import asdict, dataclass


class CfgBase(ABC):
    dict: callable = asdict


@dataclass
class RedisCfg(CfgBase):
    """Redis configuration for order state caching and real-time updates."""

    host: str = os.getenv("REDIS_HOST", "localhost")
    port: int = int(os.getenv("REDIS_PORT", "6379"))
    db: int = int(os.getenv("REDIS_DB", "0"))
    password: str = os.getenv("REDIS_PASSWORD", "")
    decode_responses: bool = True

    @property
    def url(self) -> str:
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


@dataclass
class PostgresCfg(CfgBase):
    """PostgreSQL configuration for orders service."""

    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = os.getenv("POSTGRES_PORT", "5432")
    user: str = os.getenv("POSTGRES_USER", "user")
    password: str = os.getenv("POSTGRES_PASSWORD", "pass")
    db_name: str = os.getenv("POSTGRES_DB", "orders")


redis_cfg = RedisCfg()
postgres_cfg = PostgresCfg()
