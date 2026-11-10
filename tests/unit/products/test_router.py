from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.products.router import get_product_repository
from app.products.schemas import ProductCreate


async def test_repository_dependency_uses_shared_connection(monkeypatch, product_row):
    connection = MagicMock()
    connection.__aenter__.return_value = connection
    cursor = AsyncMock()
    cursor.fetchall.return_value = [product_row]
    connection.execute = AsyncMock(return_value=cursor)
    factory = AsyncMock(return_value=connection)
    monkeypatch.setattr("app.products.router.get_connection", factory)

    products = await get_product_repository().list()

    assert products == [product_row]
    factory.assert_awaited_once_with()


def test_list_products(client, repository, product_row):
    repository.list.return_value = [product_row]

    response = client.get("/products")

    assert response.status_code == 200
    assert response.json() == [product_row]
    repository.list.assert_awaited_once_with()


def test_list_products_empty(client, repository):
    repository.list.return_value = []

    response = client.get("/products")

    assert response.status_code == 200
    assert response.json() == []


def test_create_product(client, repository, product_data, product_row):
    repository.create.return_value = product_row

    response = client.post("/products", json=product_data)

    assert response.status_code == 201
    assert response.json() == product_row
    repository.create.assert_awaited_once_with(ProductCreate(**product_data))


@pytest.mark.parametrize(
    "changes",
    [{"name": ""}, {"price": "0.00"}, {"stock": -1}, {"category": None}],
)
def test_create_rejects_invalid_product(client, repository, product_data, changes):
    response = client.post("/products", json={**product_data, **changes})

    assert response.status_code == 422
    repository.create.assert_not_awaited()


def test_create_requires_all_fields(client, repository):
    response = client.post("/products", json={})

    assert response.status_code == 422
    repository.create.assert_not_awaited()


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        ({"stock": 0}, {"stock": 0}),
        ({"price": "12.50"}, {"price": Decimal("12.50")}),
        (
            {"name": "New keyboard", "stock": 5},
            {"name": "New keyboard", "stock": 5},
        ),
    ],
)
def test_update_only_supplied_fields(
    client, repository, product_row, changes, expected
):
    updated = {**product_row, **changes}
    repository.update.return_value = updated

    response = client.patch("/products/1", json=changes)

    assert response.status_code == 200
    assert response.json() == updated
    repository.update.assert_awaited_once_with(1, expected)


def test_update_missing_product(client, repository):
    repository.update.return_value = None

    response = client.patch("/products/999", json={"stock": 0})

    assert response.status_code == 404
    assert response.json() == {"detail": "Product not found"}
    repository.update.assert_awaited_once_with(999, {"stock": 0})


@pytest.mark.parametrize(
    "changes",
    [{}, {"name": None}, {"stock": None}, {"stock": 0, "description": None}],
)
def test_update_rejects_empty_or_null_changes(client, repository, changes):
    response = client.patch("/products/1", json=changes)

    assert response.status_code == 422
    assert response.json() == {"detail": "Provide at least one non-null field"}
    repository.update.assert_not_awaited()


@pytest.mark.parametrize("changes", [{"price": "-1"}, {"stock": -1}, {"name": ""}])
def test_update_rejects_invalid_values(client, repository, changes):
    response = client.patch("/products/1", json=changes)

    assert response.status_code == 422
    repository.update.assert_not_awaited()


def test_update_requires_integer_id(client, repository):
    response = client.patch("/products/invalid", json={"stock": 1})

    assert response.status_code == 422
    repository.update.assert_not_awaited()
