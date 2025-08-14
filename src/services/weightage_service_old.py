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
                
                result = await self.db_manager.update_document(
                    collection_name=self.collection_name,
                    filter_query=filter_query,
                    update_query=update_query,
                    upsert=True
                )
                
                logger.info(f"Updated weightage for session {session_id}")
            else:
                # Store as global default
                # First deactivate any existing global defaults
                await self.db_manager.update_many(
                    collection_name=self.collection_name,
                    filter_query={"session_id": None, "is_active": True},
                    update_query={"$set": {"is_active": False}}
                )
                
                # Insert new global default
                result = await self.db_manager.insert_document(
                    collection_name=self.collection_name,
                    document=document
                )
                
                logger.info("Set global default weightage parameters")
            
            return weightage
            
        except Exception as e:
            logger.error(f"Error storing weightage parameters: {e}")
            raise Exception(f"Failed to store weightage parameters: {e}")
    
    async def get_weightage(self, session_id: Optional[str] = None) -> WeightageParameters:
        """
        Retrieve weightage parameters.
        
        Args:
            session_id: Optional session ID for session-specific weightage
            
        Returns:
            WeightageParameters (session-specific, global default, or system default)
        """
        try:
            # First try to get session-specific weightage if session_id provided
            if session_id:
                session_result = await self.db_manager.find_document(
                    collection_name=self.collection_name,
                    filter_query={"session_id": session_id, "is_active": True}
                )
                
                if session_result:
                    logger.info(f"Retrieved session-specific weightage for {session_id}")
                    return WeightageParameters(**session_result["weightage"])
            
            # Try to get global default
            global_result = await self.db_manager.find_document(
                collection_name=self.collection_name,
                filter_query={"session_id": None, "is_active": True}
            )
            
            if global_result:
                logger.info("Retrieved global default weightage")
                return WeightageParameters(**global_result["weightage"])
            
            # Return system default if nothing found
            logger.info("Using system default weightage parameters")
            return WeightageParameters()
            
        except Exception as e:
            logger.error(f"Error retrieving weightage parameters: {e}")
            # Return default on error
            return WeightageParameters()
    
    async def get_weightage_history(self, session_id: Optional[str] = None) -> list:
        """
        Get history of weightage parameter changes.
        
        Args:
            session_id: Optional session ID to filter history
            
        Returns:
            List of historical weightage parameter records
        """
        try:
            filter_query = {}
            if session_id:
                filter_query["session_id"] = session_id
            
            history = await self.db_manager.find_documents(
                collection_name=self.collection_name,
                filter_query=filter_query,
                sort_by=[("created_at", -1)],
                limit=50
            )
            
            return list(history)
            
        except Exception as e:
            logger.error(f"Error retrieving weightage history: {e}")
            return []
    
    async def delete_session_weightage(self, session_id: str) -> bool:
        """
        Delete session-specific weightage parameters.
        
        Args:
            session_id: Session ID to delete weightage for
            
        Returns:
            True if deleted successfully
        """
        try:
            result = await self.db_manager.update_many(
                collection_name=self.collection_name,
                filter_query={"session_id": session_id, "is_active": True},
                update_query={"$set": {"is_active": False, "deleted_at": datetime.utcnow()}}
            )
            
            logger.info(f"Deleted weightage parameters for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting session weightage: {e}")
            return False
