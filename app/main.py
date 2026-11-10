from fastapi import FastAPI, HTTPException
from psycopg import sql

from app.db import get_connection
from app.schemas import Product, ProductCreate, ProductUpdate

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

@app.patch("/products/{product_id}", response_model=Product)
async def update_product(product_id: int, changes: ProductUpdate):
    data = changes.model_dump(exclude_unset=True)

    if not data or any(value is None for value in data.values()):
        raise HTTPException(422, "Provide at least one non-null field")

    fields = sql.SQL(", ").join(
        sql.SQL("{} = %s").format(sql.Identifier(key))
        for key in data
    )

    query = sql.SQL(
        "UPDATE products SET {} WHERE id = %s RETURNING *"
    ).format(fields)

    async with await get_connection() as conn:
        cursor = await conn.execute(
            query,
            [*data.values(), product_id],
        )
        product = await cursor.fetchone()

    if product is None:
        raise HTTPException(404, "Product not found")

    return product


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000
    )