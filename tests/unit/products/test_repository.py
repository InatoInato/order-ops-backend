from unittest.mock import AsyncMock, MagicMock

import pytest

from app.products.repository import ProductRepository
from app.products.schemas import ProductCreate


@pytest.fixture
def database():
    connection = MagicMock()
    connection.__aenter__.return_value = connection
    cursor = AsyncMock()
    connection.execute = AsyncMock(return_value=cursor)
    factory = AsyncMock(return_value=connection)
    return factory, connection, cursor


async def test_list_products(database, product_row):
    factory, connection, cursor = database
    cursor.fetchall.return_value = [product_row]

    result = await ProductRepository(factory).list()

    assert result == [product_row]
    factory.assert_awaited_once_with()
    connection.execute.assert_awaited_once_with("SELECT * FROM products ORDER BY id")
    cursor.fetchall.assert_awaited_once_with()
    connection.__aexit__.assert_awaited_once_with(None, None, None)


async def test_create_uses_parameters(database, product_data, product_row):
    factory, connection, cursor = database
    product = ProductCreate(**{**product_data, "name": "Robert'); DROP TABLE products;--"})
    cursor.fetchone.return_value = product_row

    result = await ProductRepository(factory).create(product)

    assert result == product_row
    query, parameters = connection.execute.await_args.args
    assert " ".join(query.split()) == (
        "INSERT INTO products (name, category, description, price, stock) "
        "VALUES (%s, %s, %s, %s, %s) RETURNING *"
    )
    assert product.name not in query
    assert parameters == (
        product.name, product.category, product.description, product.price, product.stock
    )
    cursor.fetchone.assert_awaited_once_with()
    connection.__aexit__.assert_awaited_once_with(None, None, None)


@pytest.mark.parametrize("found", [True, False])
async def test_update_uses_requested_columns_and_parameters(database, product_row, found):
    factory, connection, cursor = database
    expected = product_row if found else None
    cursor.fetchone.return_value = expected
    name = "Robert'); DROP TABLE products;--"

    result = await ProductRepository(factory).update(7, {"name": name, "stock": 0})

    assert result == expected
    query, parameters = connection.execute.await_args.args
    assert query.as_string() == (
        'UPDATE products SET "name" = %s, "stock" = %s WHERE id = %s RETURNING *'
    )
    assert parameters == [name, 0, 7]
    cursor.fetchone.assert_awaited_once_with()
    connection.__aexit__.assert_awaited_once_with(None, None, None)


@pytest.mark.parametrize("operation", ["list", "create", "update"])
async def test_query_failure_exits_transaction(database, product_data, operation):
    factory, connection, _ = database
    error = RuntimeError("Database unavailable")
    connection.execute.side_effect = error
    repository = ProductRepository(factory)
    arguments = {
        "list": (),
        "create": (ProductCreate(**product_data),),
        "update": (1, {"stock": 0}),
    }

    with pytest.raises(RuntimeError, match="Database unavailable"):
        await getattr(repository, operation)(*arguments[operation])

    exception_type, exception, _ = connection.__aexit__.await_args.args
    assert exception_type is RuntimeError
    assert exception is error
