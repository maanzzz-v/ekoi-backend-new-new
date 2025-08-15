"""Session management service for chat-based resume search."""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from core.database import db_manager
from models.schemas import ChatSession, ChatMessage, MessageType
from utils.logger import get_logger

logger = get_logger(__name__)


class SessionService:
    """Service for managing chat sessions and messages."""
    
    def __init__(self):
        self.collection_name = "chat_sessions"
    
    async def create_session(self, title: Optional[str] = None, initial_message: Optional[str] = None) -> ChatSession:
        """Create a new chat session."""
        try:
            session_id = str(uuid.uuid4())
            
            # Generate title if not provided
            if not title:
                if initial_message:
                    # Create a title from the first few words of the initial message
                    words = initial_message.split()[:6]
                    title = " ".join(words) + ("..." if len(initial_message.split()) > 6 else "")
                else:
                    title = f"Resume Search Session {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
            
            session = ChatSession(
                id=session_id,
                title=title,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                messages=[],
                context={},
                is_active=True
            )
            
            # Add initial message if provided
            if initial_message:
                initial_msg = ChatMessage(
                    id=str(uuid.uuid4()),
                    type=MessageType.USER,
                    content=initial_message,
                    timestamp=datetime.utcnow()
                )
                session.messages.append(initial_msg)
            
            # Store in database
            collection = db_manager.get_collection(self.collection_name)
            session_dict = session.dict()
            session_dict["_id"] = session_id
            
            await collection.insert_one(session_dict)
            
            logger.info(f"Created new chat session: {session_id}")
            return session
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a session by ID."""
        try:
            collection = db_manager.get_collection(self.collection_name)
            session_doc = await collection.find_one({"_id": session_id})
            
            if not session_doc:
                return None
            
            # Convert back to ChatSession model
            session_doc.pop("_id", None)  # Remove MongoDB _id
            return ChatSession(**session_doc)
            
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None
    
    async def list_sessions(self, limit: int = 50, skip: int = 0, active_only: bool = True) -> List[ChatSession]:
        """List all sessions."""
        try:
            collection = db_manager.get_collection(self.collection_name)
            
            # Build query
            query = {}
            if active_only:
                query["is_active"] = True
            
            # Get sessions sorted by updated_at (most recent first)
            cursor = collection.find(query).sort("updated_at", -1).skip(skip).limit(limit)
            sessions = []
            
            async for session_doc in cursor:
                session_doc.pop("_id", None)
                sessions.append(ChatSession(**session_doc))
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []
    
    async def add_message(self, session_id: str, message_type: MessageType, content: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[ChatMessage]:
        """Add a message to a session."""
        try:
            message = ChatMessage(
                id=str(uuid.uuid4()),
                type=message_type,
                content=content,
                timestamp=datetime.utcnow(),
                metadata=metadata
            )
            
            collection = db_manager.get_collection(self.collection_name)
            
            # Update session with new message and updated timestamp
            result = await collection.update_one(
                {"_id": session_id},
                {
                    "$push": {"messages": message.dict()},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            if result.modified_count == 0:
                logger.warning(f"Session {session_id} not found or not updated")
                return None
            
            logger.info(f"Added message to session {session_id}")
            return message
            
        except Exception as e:
            logger.error(f"Error adding message to session {session_id}: {e}")
            return None
    
    async def update_session_context(self, session_id: str, context: Dict[str, Any]) -> bool:
        """Update session context with search results or other data."""
        try:
            collection = db_manager.get_collection(self.collection_name)
            
            # First check if session exists
            session_exists = await collection.find_one({"_id": session_id})
            if not session_exists:
                logger.error(f"Session {session_id} does not exist, cannot update context")
                return False
            
            # Get existing context and merge with new data
            existing_context = session_exists.get('context', {})
            merged_context = {**existing_context, **context}
            
            result = await collection.update_one(
                {"_id": session_id},
                {
                    "$set": {
                        "context": merged_context,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"Session context update result: modified_count={result.modified_count}")
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating session context {session_id}: {e}")
            import traceback
            logger.error(f"Update context traceback: {traceback.format_exc()}")
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session (mark as inactive)."""
        try:
            collection = db_manager.get_collection(self.collection_name)
            
            result = await collection.update_one(
                {"_id": session_id},
                {
                    "$set": {
                        "is_active": False,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False
    
    async def get_session_count(self, active_only: bool = True) -> int:
        """Get total count of sessions."""
        try:
            collection = db_manager.get_collection(self.collection_name)
            
            query = {}
            if active_only:
                query["is_active"] = True
            
            return await collection.count_documents(query)
            
        except Exception as e:
            logger.error(f"Error counting sessions: {e}")
            return 0


# Global session service instance
session_service = SessionService()
