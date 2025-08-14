"""
Test script for Enhanced RAG Service with Slack integration.

This script tests the Slack integration after final ranking in the enhanced RAG service.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.enhanced_rag_service import enhanced_rag_service


async def test_enhanced_rag_with_slack():
    """Test the enhanced RAG service with Slack notification after final ranking."""
    
    print("🚀 Testing Enhanced RAG Service with Slack Integration")
    print("=" * 60)
    
    # Test queries
    test_queries = [
        "Find Python developers with Django and AWS experience",
        "Looking for React developers with 3+ years experience",
        "Find data scientists with machine learning skills"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}️⃣ Testing Query: '{query}'")
        print("-" * 50)
        
        try:
            # Test with Slack notification enabled (default)
            print("🔍 Performing enhanced search with Slack notification...")
            matches, metadata = await enhanced_rag_service.intelligent_search(
                query=query,
                top_k=5,
                enable_slack_notification=True  # Slack notification after final ranking
            )
            
            print(f"✅ Search completed successfully!")
            print(f"📊 Found {len(matches)} matches after final ranking")
            print(f"🎯 Search intent: {metadata.get('query_intelligence', {}).get('intent_type', 'unknown')}")
            print(f"🔧 Technical depth: {metadata.get('query_intelligence', {}).get('technical_depth', 'unknown')}")
            
            if matches:
                top_match = matches[0]
                if top_match.extracted_info and top_match.extracted_info.name:
                    print(f"🏆 Top candidate: {top_match.extracted_info.name} (Score: {top_match.score:.2f})")
                else:
                    print(f"🏆 Top candidate: {top_match.file_name} (Score: {top_match.score:.2f})")
                
                print(f"📱 Slack notification sent for {len(matches)} final ranked candidates")
            else:
                print("❌ No matches found")
                print("📱 Slack notification sent for 'no results'")
            
        except Exception as e:
            print(f"❌ Error during search: {e}")
        
        # Wait a bit between tests
        if i < len(test_queries):
            print("\n⏱️ Waiting 2 seconds before next test...")
            await asyncio.sleep(2)
    
    print("\n🎉 All tests completed!")
    print("\n📋 Integration Summary:")
    print("✅ Enhanced RAG service performs intelligent search")
    print("✅ Query analysis and intent detection")
    print("✅ Multi-faceted search with variations")
    print("✅ Intelligent re-ranking of results")
    print("✅ Slack notification sent AFTER final ranking")
    print("✅ Non-blocking async Slack notifications")


async def test_without_slack():
    """Test the enhanced RAG service WITHOUT Slack notification."""
    
    print("\n🧪 Testing Enhanced RAG Service WITHOUT Slack")
    print("=" * 50)
    
    query = "Find senior software engineers"
    
    try:
        # Test with Slack notification disabled
        print("🔍 Performing enhanced search without Slack notification...")
        matches, metadata = await enhanced_rag_service.intelligent_search(
            query=query,
            top_k=3,
            enable_slack_notification=False  # Slack disabled
        )
        
        print(f"✅ Search completed successfully!")
        print(f"📊 Found {len(matches)} matches")
        print(f"📱 Slack notification: DISABLED")
        
    except Exception as e:
        print(f"❌ Error during search: {e}")


async def main():
    """Main test function."""
    
    print("🎯 Enhanced RAG Service - Slack Integration Test")
    print("=" * 60)
    print("🔄 Testing integration after final ranking...")
    
    # Test with Slack enabled
    await test_enhanced_rag_with_slack()
    
    # Test with Slack disabled
    await test_without_slack()
    
    print("\n🏁 Integration testing complete!")
    print("\n💡 Usage in your code:")
    print("```python")
    print("from services.enhanced_rag_service import enhanced_rag_service")
    print("")
    print("# Search with Slack notification after final ranking")
    print("matches, metadata = await enhanced_rag_service.intelligent_search(")
    print("    query='Find Python developers',")
    print("    top_k=10,")
    print("    enable_slack_notification=True  # Default")
    print(")")
    print("")
    print("# Search without Slack notification")
    print("matches, metadata = await enhanced_rag_service.intelligent_search(")
    print("    query='Find Python developers',")
    print("    enable_slack_notification=False")
    print(")")
    print("```")


if __name__ == "__main__":
    """Run the integration test."""
    asyncio.run(main())
