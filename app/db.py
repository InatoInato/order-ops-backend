import os
import psycopg
from psycopg.rows import dict_row


async def get_connection():
    return await psycopg.AsyncConnection.connect(
        os.environ["DATABASE_URL"],
        row_factory=dict_row,
    )