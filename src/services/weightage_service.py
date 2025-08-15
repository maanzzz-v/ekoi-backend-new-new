"""Service for managing weightage parameters for resume ranking."""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from models.schemas import WeightageParameters
from core.database import db_manager
from utils.logger import get_logger

logger = get_logger(__name__)


class WeightageService:
    """Service for managing weightage parameters."""
    
    def __init__(self):
        """Initialize the weightage service."""
        self.collection_name = "weightage_settings"
        
    async def set_weightage(
        self, 
        weightage: WeightageParameters, 
        session_id: Optional[str] = None
    ) -> WeightageParameters:
        """
        Store weightage parameters.
        
        Args:
            weightage: WeightageParameters to store
            session_id: Optional session ID for session-specific weightage
            
        Returns:
            WeightageParameters that were stored
        """
        try:
            collection = db_manager.get_collection(self.collection_name)
            
            # Create document to store
            document = {
                "weightage": weightage.dict(),
                "session_id": session_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True
            }
            
            # If session_id provided, update existing or create new
            if session_id:
                filter_query = {"session_id": session_id, "is_active": True}
                update_query = {
                    "$set": {
                        "weightage": weightage.dict(),
                        "updated_at": datetime.utcnow()
                    }
                }
                
                result = await collection.update_one(
                    filter_query,
                    update_query,
                    upsert=True
                )
                
                logger.info(f"Updated weightage for session {session_id}")
            else:
                # Store as global default
                # First deactivate any existing global defaults
                await collection.update_many(
                    {"session_id": None, "is_active": True},
                    {"$set": {"is_active": False}}
                )
                
                # Insert new global default
                result = await collection.insert_one(document)
                
                logger.info("Set global default weightage parameters")
            
            return weightage
            
        except Exception as e:
            logger.error(f"Error setting weightage parameters: {e}")
            raise
    
    async def get_weightage(self, session_id: Optional[str] = None) -> WeightageParameters:
        """
        Get weightage parameters.
        
        Args:
            session_id: Optional session ID to get session-specific weightage
            
        Returns:
            WeightageParameters (session-specific if available, otherwise global default)
        """
        try:
            collection = db_manager.get_collection(self.collection_name)
            
            # Try to get session-specific weightage first
            if session_id:
                session_result = await collection.find_one({
                    "session_id": session_id,
                    "is_active": True
                })
                
                if session_result:
                    return WeightageParameters(**session_result["weightage"])
            
            # Get global default
            global_result = await collection.find_one({
                "session_id": None,
                "is_active": True
            })
            
            if global_result:
                return WeightageParameters(**global_result["weightage"])
            
            # Return default if nothing found
            logger.info("No weightage parameters found, returning defaults")
            return WeightageParameters()
            
        except Exception as e:
            logger.error(f"Error getting weightage parameters: {e}")
            # Return default values on error
            return WeightageParameters()
    
    async def get_weightage_history(
        self, 
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> list:
        """
        Get history of weightage parameter changes.
        
        Args:
            session_id: Optional session ID to filter by
            limit: Maximum number of records to return
            
        Returns:
            List of weightage parameter history records
        """
        try:
            collection = db_manager.get_collection(self.collection_name)
            
            filter_query = {}
            if session_id:
                filter_query["session_id"] = session_id
            
            cursor = collection.find(filter_query).sort("created_at", -1).limit(limit)
            history = await cursor.to_list(length=limit)
            
            # Convert to serializable format
            for record in history:
                record["_id"] = str(record["_id"])
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting weightage history: {e}")
            return []
    
    async def delete_session_weightage(self, session_id: str) -> bool:
        """
        Delete weightage parameters for a specific session.
        
        Args:
            session_id: Session ID to delete weightage for
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            collection = db_manager.get_collection(self.collection_name)
            
            result = await collection.update_many(
                {"session_id": session_id, "is_active": True},
                {"$set": {"is_active": False, "deleted_at": datetime.utcnow()}}
            )
            
            logger.info(f"Deactivated weightage parameters for session {session_id}")
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting session weightage: {e}")
            return False


# Global weightage service instance
weightage_service = WeightageService()
