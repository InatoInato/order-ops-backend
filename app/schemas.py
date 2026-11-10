
from decimal import Decimal

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    category: str = Field(min_length=1, max_length=20)
    description: str = Field(min_length=1, max_length=400)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    stock: int = Field(ge=0)


class Product(ProductCreate):
    id: int

class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    category: str | None = Field(default=None, min_length=1, max_length=20)
    description: str | None = Field(default=None, min_length=1, max_length=400)
    price: Decimal | None = Field(
        default=None, gt=0, max_digits=10, decimal_places=2
    )
    stock: int | None = Field(default=None, ge=0)