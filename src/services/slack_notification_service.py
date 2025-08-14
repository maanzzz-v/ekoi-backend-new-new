"""Slack notification service for sending shortlisted resume matches."""

import logging
import json
import os
from typing import List, Dict, Any, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime

from models.schemas import ResumeMatch
from utils.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)


class SlackNotificationService:
    """Service for sending resume search results to Slack channels."""
    
    def __init__(self, slack_token: str = None):
        """Initialize Slack client with token."""
        if slack_token is None:
            # Try to get from settings first, then environment
            try:
                slack_token = settings.slack_token
            except:
                slack_token = os.getenv("SLACK_TOKEN")
        
        if not slack_token:
            raise ValueError("Slack token must be provided either as parameter or SLACK_TOKEN environment variable")
            
        self.client = WebClient(token=slack_token)
        self.default_channel = "#test_message"
    
    async def send_shortlisted_resumes(
        self, 
        matches: List[ResumeMatch], 
        search_query: str,
        metadata: Optional[Dict[str, Any]] = None,
        channel: str = None
    ) -> bool:
        """
        Send shortlisted resume matches to Slack channel.
        
        Args:
            matches: List of ResumeMatch objects from vector DB retrieval
            search_query: Original search query
            metadata: Additional search metadata
            channel: Slack channel (defaults to #test_message)
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        try:
            channel = channel or self.default_channel
            
            # Format the message with shortlisted resumes
            formatted_message = self._format_resume_matches(matches, search_query, metadata)
            
            # Send message to Slack
            response = self.client.chat_postMessage(
                channel=channel,
                text=formatted_message
            )
            
            logger.info(f"Slack message sent successfully: {response['ts']}")
            print(f"Message sent successfully: {response['ts']}")
            return True
            
        except SlackApiError as e:
            logger.error(f"Error sending Slack message: {e.response['error']}")
            print(f"Error sending message: {e.response['error']}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Slack message: {e}")
            print(f"Unexpected error: {e}")
            return False
    
    def _format_resume_matches(
        self, 
        matches: List[ResumeMatch], 
        search_query: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format resume matches into a Slack-friendly message."""
        
        # Header with search info
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_matches = len(matches)
        
        message_parts = [
            "🎯 *Resume Search Results*",
            f"📅 *Search Time:* {timestamp}",
            f"🔍 *Query:* `{search_query}`",
            f"📊 *Total Matches:* {total_matches}",
            ""
        ]
        
        # Add search metadata if available
        if metadata:
            search_intent = metadata.get("search_intent", {})
            if search_intent.get("primary_skills"):
                skills = ", ".join(search_intent["primary_skills"][:5])
                message_parts.append(f"🔧 *Detected Skills:* {skills}")
            
            if search_intent.get("experience_level") != "any":
                message_parts.append(f"📈 *Experience Level:* {search_intent['experience_level']}")
            
            message_parts.append("")
        
        # Add individual resume matches
        if matches:
            message_parts.append("📋 *Shortlisted Candidates:*")
            message_parts.append("")
            
            for i, match in enumerate(matches[:10], 1):  # Limit to top 10 for readability
                candidate_info = self._format_single_candidate(match, i)
                message_parts.append(candidate_info)
                message_parts.append("")
        else:
            message_parts.append("❌ *No matching candidates found.*")
        
        # Add footer
        message_parts.extend([
            "---",
            "🤖 *Sent by Resume Indexer AI*",
            f"💾 *Vector DB Search Completed*"
        ])
        
        return "\n".join(message_parts)
    
    def _format_single_candidate(self, match: ResumeMatch, rank: int) -> str:
        """Format a single candidate's information."""
        # Basic info
        name = "Unknown Candidate"
        skills = []
        experience_summary = "Experience not available"
        score_percentage = round(match.score * 100, 1)
        
        # Extract info if available
        if match.extracted_info:
            name = match.extracted_info.name or f"Candidate {rank}"
            skills = match.extracted_info.skills[:6] if match.extracted_info.skills else []
            
            if match.extracted_info.experience:
                exp_count = len(match.extracted_info.experience)
                experience_summary = f"{exp_count} role{'s' if exp_count != 1 else ''} listed"
        
        # Build candidate block
        candidate_lines = [
            f"*{rank}. {name}* (Match: {score_percentage}%)",
            f"📄 *File:* {match.file_name}"
        ]
        
        if skills:
            skills_text = ", ".join(skills)
            if len(skills_text) > 100:  # Truncate if too long
                skills_text = skills_text[:97] + "..."
            candidate_lines.append(f"🔧 *Skills:* {skills_text}")
        
        candidate_lines.append(f"💼 *Experience:* {experience_summary}")
        
        # Add relevant text preview if available
        if match.relevant_text:
            preview = match.relevant_text[:150]
            if len(match.relevant_text) > 150:
                preview += "..."
            candidate_lines.append(f"📝 *Preview:* _{preview}_")
        
        return "\n".join(candidate_lines)
    
    async def send_search_summary(
        self, 
        search_query: str, 
        total_results: int,
        search_metadata: Dict[str, Any],
        channel: str = None
    ) -> bool:
        """Send a quick search summary without full candidate details."""
        try:
            channel = channel or self.default_channel
            
            # Create summary message
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            message = f"""🔍 *Resume Search Completed*
📅 *Time:* {timestamp}
🎯 *Query:* `{search_query}`
📊 *Results:* {total_results} candidates found

🤖 *AI Processing Complete* ✅"""
            
            response = self.client.chat_postMessage(
                channel=channel,
                text=message
            )
            
            logger.info(f"Search summary sent to Slack: {response['ts']}")
            return True
            
        except SlackApiError as e:
            logger.error(f"Error sending search summary: {e.response['error']}")
            return False
    
    async def send_custom_message(self, message: str, channel: str = None) -> bool:
        """Send a custom message to Slack."""
        try:
            channel = channel or self.default_channel
            
            response = self.client.chat_postMessage(
                channel=channel,
                text=message
            )
            
            logger.info(f"Custom message sent to Slack: {response['ts']}")
            return True
            
        except SlackApiError as e:
            logger.error(f"Error sending custom message: {e.response['error']}")
            return False
    
    async def send_json_data(
        self, 
        matches: List[ResumeMatch], 
        search_query: str,
        channel: str = None,
        include_raw_json: bool = False
    ) -> bool:
        """Send resume matches with optional raw JSON data."""
        try:
            channel = channel or self.default_channel
            
            # Main formatted message
            main_message = self._format_resume_matches(matches, search_query)
            
            # Send main message
            response = self.client.chat_postMessage(
                channel=channel,
                text=main_message
            )
            
            # Optionally send raw JSON as a file/snippet
            if include_raw_json and matches:
                json_data = {
                    "search_query": search_query,
                    "timestamp": datetime.now().isoformat(),
                    "total_matches": len(matches),
                    "matches": [
                        {
                            "id": match.id,
                            "file_name": match.file_name,
                            "score": match.score,
                            "extracted_info": match.extracted_info.dict() if match.extracted_info else None,
                            "relevant_text": match.relevant_text
                        }
                        for match in matches
                    ]
                }
                
                # Send as code block for better formatting
                json_text = f"```json\n{json.dumps(json_data, indent=2)}\n```"
                
                self.client.chat_postMessage(
                    channel=channel,
                    text="📄 *Raw JSON Data:*\n" + json_text
                )
            
            logger.info(f"Resume data sent to Slack: {response['ts']}")
            return True
            
        except SlackApiError as e:
            logger.error(f"Error sending JSON data: {e.response['error']}")
            return False


# Global instance - Initialize with settings
try:
    slack_notification_service = SlackNotificationService(slack_token=settings.slack_token)
except Exception as e:
    logger.warning(f"Failed to initialize Slack service: {e}")
    slack_notification_service = None


# Example usage function
async def send_matches_to_slack(
    matches: List[ResumeMatch], 
    search_query: str, 
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Convenience function to send matches to Slack.
    
    This can be called from anywhere in your codebase after getting matches from vector DB.
    
    Example usage:
        # After getting matches from RAG service
        matches, metadata = await rag_service.enhanced_search(query)
        
        # Send to Slack
        await send_matches_to_slack(matches, query, metadata)
    """
    success = await slack_notification_service.send_shortlisted_resumes(
        matches=matches,
        search_query=search_query,
        metadata=metadata
    )
    
    if success:
        logger.info(f"Successfully sent {len(matches)} matches to Slack")
    else:
        logger.error("Failed to send matches to Slack")
    
    return success


if __name__ == "__main__":
    """
    Test the Slack notification service.
    """
    import asyncio
    from models.schemas import ResumeMatch, ExtractedInfo
    
    # Create sample data for testing
    sample_extracted_info = ExtractedInfo(
        name="John Doe",
        email="john.doe@example.com",
        skills=["Python", "Django", "AWS", "React"],
        experience=[{"description": "Senior Developer at Tech Corp"}],
        summary="Experienced Python developer with 5+ years"
    )
    
    sample_match = ResumeMatch(
        id="test_resume_1",
        file_name="john_doe_resume.pdf",
        score=0.89,
        extracted_info=sample_extracted_info,
        relevant_text="Senior Python Developer with extensive experience in web development"
    )
    
    # Test sending to Slack
    async def test_slack():
        await send_matches_to_slack(
            matches=[sample_match],
            search_query="Find Python developers with Django experience",
            metadata={
                "search_intent": {
                    "primary_skills": ["python", "django"],
                    "experience_level": "senior"
                }
            }
        )
    
    # Run test
    # asyncio.run(test_slack())
