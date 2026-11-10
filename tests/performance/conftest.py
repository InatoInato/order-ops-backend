import asyncio

import httpx2
import pytest

from app.main import app
from app.products.router import get_product_repository


class InMemoryProductRepository:
    """A yielding repository substitute; timings exclude PostgreSQL and sockets."""

    def __init__(self, product_row):
        self.rows = [{**product_row, "id": index} for index in range(1, 101)]

    async def list(self):
        await asyncio.sleep(0)
        return self.rows

    async def create(self, product):
        await asyncio.sleep(0)
        row = {"id": len(self.rows) + 1, **product.model_dump()}
        self.rows.append(row)
        return row

    async def update(self, product_id, changes):
        await asyncio.sleep(0)
        for row in self.rows:
            if row["id"] == product_id:
                row.update(changes)
                return row
        return None


@pytest.fixture
def performance_repository(product_row):
    return InMemoryProductRepository(product_row)


@pytest.fixture
async def performance_client(performance_repository):
    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_product_repository] = lambda: performance_repository
    try:
        transport = httpx2.ASGITransport(app=app)
        async with httpx2.AsyncClient(
            transport=transport, base_url="http://performance.test"
        ) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
