from collections.abc import Awaitable, Callable
from typing import Any

from psycopg import AsyncConnection, sql

from app.products.schemas import ProductCreate


class ProductRepository:
    """Execute product queries using one transaction per operation."""

    def __init__(
        self, connection_factory: Callable[[], Awaitable[AsyncConnection]]
    ) -> None:
        self._connection_factory = connection_factory

    async def list(self) -> list[dict[str, Any]]:
        async with await self._connection_factory() as conn:
            cursor = await conn.execute("SELECT * FROM products ORDER BY id")
            return await cursor.fetchall()

    async def create(self, product: ProductCreate) -> dict[str, Any]:
        async with await self._connection_factory() as conn:
            cursor = await conn.execute(
                """
                INSERT INTO products
                    (name, category, description, price, stock)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    product.name,
                    product.category,
                    product.description,
                    product.price,
                    product.stock,
                ),
            )
            return await cursor.fetchone()

    async def update(
        self, product_id: int, changes: dict[str, Any]
    ) -> dict[str, Any] | None:
        fields = sql.SQL(", ").join(
            sql.SQL("{} = %s").format(sql.Identifier(key)) for key in changes
        )
        query = sql.SQL(
            "UPDATE products SET {} WHERE id = %s RETURNING *"
        ).format(fields)

        async with await self._connection_factory() as conn:
            cursor = await conn.execute(query, [*changes.values(), product_id])
            return await cursor.fetchone()
