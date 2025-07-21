from pydantic import BaseModel
from typing import List


class SizeDetail(BaseModel):
    size: str
    quantity: int


class ProductCreate(BaseModel):
    name: str
    price: float
    sizes: List[SizeDetail]


class ProductOut(BaseModel):
    id: str
