from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.db import get_connection
from app.products.repository import ProductRepository
from app.products.schemas import Product, ProductCreate, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


def get_product_repository() -> ProductRepository:
    return ProductRepository(get_connection)


Repository = Annotated[ProductRepository, Depends(get_product_repository)]


@router.get("", response_model=list[Product])
async def get_products(repository: Repository):
    return await repository.list()


@router.post("", response_model=Product, status_code=201)
async def create_product(product: ProductCreate, repository: Repository):
    return await repository.create(product)


@router.patch("/{product_id}", response_model=Product)
async def update_product(
    product_id: int, changes: ProductUpdate, repository: Repository
):
    data = changes.model_dump(exclude_unset=True)
    if not data or any(value is None for value in data.values()):
        raise HTTPException(422, "Provide at least one non-null field")

    product = await repository.update(product_id, data)
    if product is None:
        raise HTTPException(404, "Product not found")
    return product
