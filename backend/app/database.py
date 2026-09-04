"""
Asynchronous MongoDB Database Manager (Motor) with Instant Offline Fallback
"""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config.settings import settings

logger = logging.getLogger("backend_db")


class MongoManager:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    is_available: bool = False

    @classmethod
    async def connect(cls):
        """Initializes connection to MongoDB with short timeout check."""
        try:
            temp_client = AsyncIOMotorClient(settings.MONGO_URI, serverSelectionTimeoutMS=1000)
            await temp_client.admin.command("ping")
            cls.client = temp_client
            cls.db = cls.client[settings.MONGO_DB_NAME]
            cls.is_available = True
            logger.info(f"Connected to MongoDB at {settings.MONGO_URI} (DB: {settings.MONGO_DB_NAME})")
        except Exception as e:
            cls.client = None
            cls.db = None
            cls.is_available = False
            logger.info(f"MongoDB not reachable on {settings.MONGO_URI} ({e}). Seamlessly using Embedded Real-Time Store.")

    @classmethod
    async def close(cls):
        """Closes MongoDB connection."""
        if cls.client:
            cls.client.close()
            logger.info("MongoDB connection closed.")
        cls.client = None
        cls.db = None
        cls.is_available = False

    @classmethod
    def get_db(cls) -> Optional[AsyncIOMotorDatabase]:
        if not cls.is_available:
            return None
        return cls.db

    @classmethod
    async def is_connected(cls) -> bool:
        return cls.is_available


async def get_database() -> Optional[AsyncIOMotorDatabase]:
    return MongoManager.get_db()
