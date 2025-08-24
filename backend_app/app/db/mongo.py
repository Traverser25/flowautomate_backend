# app/db/mongo.py
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import get_settings

settings = get_settings()

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

mongo = MongoDB()

async def connect_to_mongo():
    """Initialize MongoDB connection"""
    mongo.client = AsyncIOMotorClient(settings.MONGO_URL)
    mongo.db = mongo.client[settings.MONGO_DB]
    # Create unique index on username for users
    await mongo.db.users.create_index("username", unique=True)
    print("Connected to MongoDB")


async def close_mongo_connection():
    """Close MongoDB connection"""
    if mongo.client:
        mongo.client.close()
        print("MongoDB connection closed")
