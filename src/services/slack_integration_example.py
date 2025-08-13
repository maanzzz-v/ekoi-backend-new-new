"""
Example integration of Slack notifications with the existing RAG service.

This file demonstrates how to integrate the Slack notification service
with your existing resume search functionality without modifying the core code.
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from services.rag_service import rag_service
from services.slack_notification_service import slack_notification_service, send_matches_to_slack
from utils.logger import get_logger

logger = get_logger(__name__)


class SlackIntegratedSearchService:
    """
    Wrapper service that integrates Slack notifications with resume search.
    
    This service acts as a bridge between your existing RAG service and Slack,
    without modifying any existing code.
    """
    
    def __init__(self):
        self.slack_service = slack_notification_service
    
    async def search_and_notify_slack(
        self, 
        query: str, 
        top_k: int = 10, 
        filters: Optional[Dict[str, Any]] = None,
        slack_channel: str = "#test_message",
        notify_immediately: bool = True
    ):
        """
        Perform resume search and send results to Slack.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filters: Additional search filters
            slack_channel: Slack channel to send results to
            notify_immediately: Whether to send notification immediately after search
            
        Returns:
            Tuple of (matches, metadata, slack_success)
        """
        try:
            logger.info(f"Starting integrated search and Slack notification for: '{query}'")
            
            # Step 1: Perform the enhanced search using existing RAG service
            matches, metadata = await rag_service.enhanced_search(
                query=query, 
                top_k=top_k, 
                filters=filters
            )
            
            logger.info(f"Search completed: {len(matches)} matches found")
            
            # Step 2: Send results to Slack if matches found and notification enabled
            slack_success = False
            if notify_immediately:
                if matches:
                    slack_success = await self.slack_service.send_shortlisted_resumes(
                        matches=matches,
                        search_query=query,
                        metadata=metadata,
                        channel=slack_channel
                    )
                    
                    if slack_success:
                        logger.info(f"Successfully sent {len(matches)} matches to Slack channel {slack_channel}")
                    else:
                        logger.error(f"Failed to send matches to Slack channel {slack_channel}")
                else:
                    # Send "no results" message to Slack
                    no_results_message = f"""🔍 *Resume Search - No Results*
📅 *Time:* {metadata.get('timestamp', 'N/A')}
🎯 *Query:* `{query}`
❌ *No matching candidates found*

💡 *Suggestions:*
• Try broadening your search criteria
• Consider related technologies or skills
• Check for alternative job titles"""
                    
                    slack_success = await self.slack_service.send_custom_message(
                        message=no_results_message,
                        channel=slack_channel
                    )
            
            return matches, metadata, slack_success
            
        except Exception as e:
            logger.error(f"Error in integrated search and notification: {e}")
            raise
    
    async def send_existing_matches_to_slack(
        self, 
        matches, 
        search_query: str, 
        metadata: Optional[Dict[str, Any]] = None,
        channel: str = "#test_message"
    ):
        """
        Send already-obtained matches to Slack.
        
        Use this when you already have matches from a previous search
        and want to send them to Slack.
        """
        return await send_matches_to_slack(matches, search_query, metadata)


# Global instance
slack_integrated_search = SlackIntegratedSearchService()


async def example_usage():
    """
    Example of how to use the Slack-integrated search service.
    """
    # Example 1: Search and automatically send to Slack
    print("🔍 Example 1: Search with automatic Slack notification")
    matches, metadata, slack_sent = await slack_integrated_search.search_and_notify_slack(
        query="Find Python developers with Django and AWS experience",
        top_k=5,
        slack_channel="#test_message"
    )
    
    print(f"Found {len(matches)} matches, Slack notification sent: {slack_sent}")
    
    # Example 2: Use existing RAG service and then send to Slack separately
    print("\n🔍 Example 2: Separate search and notification")
    matches, metadata = await rag_service.enhanced_search(
        query="Find React developers with 3+ years experience",
        top_k=3
    )
    
    # Send to Slack separately
    slack_success = await send_matches_to_slack(
        matches=matches,
        search_query="Find React developers with 3+ years experience",
        metadata=metadata
    )
    
    print(f"Found {len(matches)} matches, Slack notification sent: {slack_success}")


# Integration helper functions for easy use
async def quick_search_and_slack(query: str, top_k: int = 5):
    """Quick function to search and send to Slack with default settings."""
    return await slack_integrated_search.search_and_notify_slack(
        query=query,
        top_k=top_k,
        slack_channel="#test_message"
    )


async def send_search_results_to_slack(matches, query: str, metadata=None):
    """Simple function to send existing search results to Slack."""
    return await send_matches_to_slack(matches, query, metadata)


if __name__ == "__main__":
    """
    Test the integration.
    """
    print("🚀 Testing Slack Integration with Resume Search")
    print("=" * 50)
    
    # Run the example
    asyncio.run(example_usage())
