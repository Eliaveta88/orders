"""Orders schemas."""

from pydantic import BaseModel


class OrderBase(BaseModel):
    pass


class OrderResponse(BaseModel):
    pass
