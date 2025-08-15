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
            # Determine if this is a local or Atlas connection
            is_local = any(host in settings.mongodb_url.lower() for host in ["localhost", "127.0.0.1", "0.0.0.0"])
            is_atlas = "mongodb.net" in settings.mongodb_url or "mongodb+srv" in settings.mongodb_url
            
            if is_local:
                # For local MongoDB, use simple connection
                logger.info("Connecting to local MongoDB...")
                self.client = AsyncIOMotorClient(
                    settings.mongodb_url,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=10000,
                    socketTimeoutMS=10000,
                )
            elif is_atlas:
                # For MongoDB Atlas, try different approaches
                logger.info("Connecting to MongoDB Atlas...")
                
                # First try: Standard Atlas connection
                try:
                    client_options = {
                        "serverSelectionTimeoutMS": 30000,
                        "connectTimeoutMS": 30000,
                        "socketTimeoutMS": 30000,
                        "maxPoolSize": 10,
                        "minPoolSize": 1,
                        "retryWrites": True,
                    }
                    
                    self.client = AsyncIOMotorClient(settings.mongodb_url, **client_options)
                    self.database = self.client[settings.mongodb_database]
                    await self.client.admin.command("ping")
                    logger.info(f"Successfully connected to MongoDB Atlas database: {settings.mongodb_database}")
                    return
                    
                except Exception as first_error:
                    logger.warning(f"First connection attempt failed: {first_error}")
                    
                    # Second try: Use modified URL without SSL verification
                    try:
                        logger.info("Trying alternative Atlas connection...")
                        base_url = settings.mongodb_url.split("?")[0] if "?" in settings.mongodb_url else settings.mongodb_url
                        alt_url = f"{base_url}?retryWrites=true&w=majority&tls=true&tlsInsecure=true"
                        
                        self.client = AsyncIOMotorClient(
                            alt_url,
                            serverSelectionTimeoutMS=30000,
                            connectTimeoutMS=30000,
                            socketTimeoutMS=30000,
                        )
                        self.database = self.client[settings.mongodb_database]
                        await self.client.admin.command("ping")
                        logger.info("Successfully connected with alternative Atlas method!")
                        return
                        
                    except Exception as second_error:
                        logger.error(f"Alternative Atlas connection failed: {second_error}")
                        
                        # Third try: Fallback to basic connection
                        try:
                            logger.info("Trying basic Atlas connection...")
                            self.client = AsyncIOMotorClient(settings.mongodb_url)
                            self.database = self.client[settings.mongodb_database]
                            await self.client.admin.command("ping")
                            logger.info("Successfully connected with basic Atlas method!")
                            return
                        except Exception as third_error:
                            logger.error(f"Basic Atlas connection failed: {third_error}")
                            raise third_error
            else:
                # For other remote MongoDB instances
                logger.info("Connecting to remote MongoDB...")
                self.client = AsyncIOMotorClient(
                    settings.mongodb_url,
                    serverSelectionTimeoutMS=15000,
                    connectTimeoutMS=15000,
                    socketTimeoutMS=15000,
                )
                self.database = self.client[settings.mongodb_database]
                await self.client.admin.command("ping")
                logger.info(f"Successfully connected to remote MongoDB database: {settings.mongodb_database}")

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            if "SSL" in str(e) or "ssl" in str(e).lower() or "_ssl.c" in str(e):
                logger.error("SSL/TLS connection issue detected.")
                logger.error("This might be due to system SSL configuration or Python SSL library issues.")
                logger.error("Consider using a different Python environment or updating SSL libraries.")
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
