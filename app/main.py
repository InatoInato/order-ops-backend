from fastapi import FastAPI

from app.db import get_connection
from app.schemas import Product, ProductCreate

import uvicorn
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="OrderOps API")


@app.get("/products", response_model=list[Product])
async def get_products():
    async with await get_connection() as conn:
        cursor = await conn.execute(
            "SELECT * FROM products ORDER BY id"
        )
        return await cursor.fetchall()


@app.post("/products", response_model=Product, status_code=201)
async def create_product(product: ProductCreate):
    async with await get_connection() as conn:
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


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000
    )