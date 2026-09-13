import os
from motor.motor_asyncio import AsyncIOMotorClient

_client = AsyncIOMotorClient(os.environ["MONGO_URL"])
db = _client[os.environ["DB_NAME"]]


def serialize(doc: dict) -> dict:
    """Strip MongoDB _id from a document (we use custom string ids everywhere)."""
    if not doc:
        return doc
    doc = dict(doc)
    doc.pop("_id", None)
    return doc
