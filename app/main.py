from fastapi import FastAPI

app = FastAPI()

products = [
    {
        "id": 1,
        "name": "iPhone 16 256GB Blue",
        "category": "Phones",
        "description": "Used iPhone 16 256GB Blue",
        "price": 623.99,
        "stock": 2,
    },
    {
        "id": 2,
        "name": "MacBook Air",
        "category": "Laptops",
        "description": "Used MacBook Air 16/256GB Space Grey",
        "stock": 5,
        "price": 528.99
    },
    {
        "id": 3,
        "name": "iPhone Duo",
        "category": "Phones",
        "description": "Brand new first fold phone by Apple!",
        "stock": 10,
        "price": 2319.99
    }
]

@app.get("/products")
def get_products():
    return products