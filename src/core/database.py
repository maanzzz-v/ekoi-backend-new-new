"""Database connection and management."""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config.settings import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """MongoDB database manager."""

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None

    async def connect(self) -> None:
        """Connect to MongoDB."""
        try:
            self.client = AsyncIOMotorClient(settings.mongodb_url)
            self.database = self.client[settings.mongodb_database]

            # Test connection
            await self.client.admin.command("ismaster")
            logger.info("Successfully connected to MongoDB")

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    def get_collection(self, collection_name: str):
        """Get a collection from the database."""
        if self.database is None:
            raise RuntimeError("Database not connected")
        return self.database[collection_name]


# Global database manager instance
db_manager = DatabaseManager()
