from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.products.repository import ProductRepository
from app.products.router import get_product_repository


@pytest.fixture
def product_data():
    return {
        "name": "Keyboard",
        "category": "Electronics",
        "description": "Mechanical keyboard",
        "price": "49.99",
        "stock": 10,
    }


@pytest.fixture
def product_row(product_data):
    return {"id": 1, **product_data}


@pytest.fixture
def repository():
    return AsyncMock(spec=ProductRepository)


@pytest.fixture
def client(repository):
    app.dependency_overrides[get_product_repository] = lambda: repository
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_product_repository, None)
