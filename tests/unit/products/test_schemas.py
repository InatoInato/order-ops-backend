from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.products.schemas import Product, ProductCreate, ProductUpdate


def test_price_is_decimal(product_data):
    product = ProductCreate(**product_data)

    assert product.price == Decimal("49.99")
    assert isinstance(product.price, Decimal)


@pytest.mark.parametrize("schema", [ProductCreate, ProductUpdate])
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", ""),
        ("name", "x" * 51),
        ("category", ""),
        ("category", "x" * 21),
        ("description", ""),
        ("description", "x" * 401),
        ("price", "0"),
        ("price", "-0.01"),
        ("price", "1.001"),
        ("price", "100000000.00"),
        ("stock", -1),
        ("stock", 1.5),
    ],
)
def test_invalid_fields(schema, field, value, product_data):
    data = product_data if schema is ProductCreate else {}

    with pytest.raises(ValidationError):
        schema(**{**data, field: value})


@pytest.mark.parametrize("schema", [ProductCreate, ProductUpdate])
def test_valid_boundaries(schema):
    product = schema(
        name="x" * 50,
        category="x" * 20,
        description="x" * 400,
        price="99999999.99",
        stock=0,
    )

    assert product.price == Decimal("99999999.99")
    assert product.stock == 0


def test_update_preserves_explicit_zero():
    assert ProductUpdate(stock=0).model_dump(exclude_unset=True) == {"stock": 0}


def test_update_distinguishes_missing_from_null():
    assert ProductUpdate().model_dump(exclude_unset=True) == {}
    assert ProductUpdate(stock=None).model_dump(exclude_unset=True) == {"stock": None}


def test_product_requires_id(product_data):
    with pytest.raises(ValidationError):
        Product(**product_data)

    assert Product(id=1, **product_data).id == 1
