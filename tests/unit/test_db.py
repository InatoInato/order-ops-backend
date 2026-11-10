from unittest.mock import AsyncMock

import pytest
from psycopg.rows import dict_row

from app.db import get_connection


async def test_connection_uses_database_url_and_dictionary_rows(monkeypatch):
    database_url = "postgresql://test:test@localhost/test"
    monkeypatch.setenv("DATABASE_URL", database_url)
    connect = AsyncMock()
    monkeypatch.setattr("app.db.psycopg.AsyncConnection.connect", connect)

    connection = await get_connection()

    assert connection is connect.return_value
    connect.assert_awaited_once_with(database_url, row_factory=dict_row)


async def test_connection_requires_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    connect = AsyncMock()
    monkeypatch.setattr("app.db.psycopg.AsyncConnection.connect", connect)

    with pytest.raises(KeyError, match="DATABASE_URL"):
        await get_connection()

    connect.assert_not_awaited()
