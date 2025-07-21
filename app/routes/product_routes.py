from fastapi import APIRouter, Query
from typing import Optional
from app.models.product_model import ProductCreate
from app.database import db

router = APIRouter()



@router.post("/products", status_code=201)
async def create_product(product: ProductCreate):
    product_dict = product.dict()
    result = await db.products.insert_one(product_dict)
    return {"id": str(result.inserted_id)}


@router.get("/products")
async def list_products(
    name: Optional[str] = None,
    size: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
):
    query = {}

    if name:
        query["name"] = {"$regex": name, "$options": "i"}

    if size:
        query["sizes"] = {
            "$elemMatch": {"size": size}
        }

    total_docs = await db.products.count_documents(query)
    cursor = db.products.find(query).skip(offset).limit(limit)

    data = []
    async for product in cursor:
        data.append({
            "id": str(product["_id"]),
            "name": product["name"],
            "price": product["price"]
        })

    return {
        "data": data,
        "page": {
            "next": offset + limit if offset + limit < total_docs else None,
            "limit": len(data),
            "previous": offset - limit if offset - limit >= 0 else None
        }
    }
