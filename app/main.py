import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

from app.products.router import router as products_router

load_dotenv()

app = FastAPI(title="OrderOps API")
app.include_router(products_router)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000)
