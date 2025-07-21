from fastapi import APIRouter, HTTPException
from app.models.order_model import OrderCreate
from app.database import db
from datetime import datetime
from bson import ObjectId, errors

router = APIRouter()


@router.post("/orders", status_code=201)
async def create_order(order: OrderCreate):
    items = []

    for item in order.items:
        try:
            product_obj_id = ObjectId(item.productId)
        except errors.InvalidId:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid productId: '{item.productId}' must be a 24-character hex string"
            )

        items.append({
            "productId": product_obj_id,
            "qty": item.qty
        })

    order_doc = {
        "userId": order.userId,
        "items": items,
        "timestamp": datetime.utcnow()
    }

    result = await db.orders.insert_one(order_doc)
    return {"id": str(result.inserted_id)}


@router.get("/orders/{user_id}")
async def get_orders(user_id: str, limit: int = 10, offset: int = 0):
    pipeline = [
        {"$match": {"userId": user_id}},
        {"$unwind": "$items"},
        {
            "$lookup": {
                "from": "products",
                "localField": "items.productId",
                "foreignField": "_id",
                "as": "product"
            }
        },
        {
            "$unwind": {
                "path": "$product",
                "preserveNullAndEmptyArrays": True
            }
        },
        {
            "$addFields": {
                "lineTotal": {
                    "$multiply": ["$items.qty", "$product.price"]
                }
            }
        },
        {
            "$group": {
                "_id": "$_id",
                "userId": {"$first": "$userId"},
                "timestamp": {"$first": "$timestamp"},
                "items": {
                    "$push": {
                        "productDetails": {
                            "id": {"$toString": "$product._id"},
                            "name": "$product.name"
                        },
                        "qty": "$items.qty"
                    }
                },
                "total": { "$sum": "$lineTotal" }
            }
        },
        {"$sort": {"_id": 1}},
        {"$skip": offset},
        {"$limit": limit}
    ]

    cursor = db.orders.aggregate(pipeline)

    orders = []
    total_amount = 0.0

    async for doc in cursor:
        order_total = round(doc.get("total", 0), 2)
        total_amount += order_total

        orders.append({
            "id": str(doc["_id"]),
            "items": doc["items"],
            "total": order_total
        })

    total_orders = await db.orders.count_documents({"userId": user_id})

    return {
        "data": orders,
        "page": {
            "next": offset + limit if offset + limit < total_orders else None,
            "limit": len(orders),
            "previous": offset - limit if offset - limit >= 0 else None
        },
        "totalOrderAmount": round(total_amount, 2)
    }
