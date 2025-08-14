# Slack Integration for Resume Indexer

This integration allows you to send shortlisted resume matches to Slack channels automatically after vector DB retrieval.

## 🚀 Quick Start

### 1. Files Created

- `slack_notification_service.py` - Main Slack service
- `slack_integration_example.py` - Integration examples
- `test_slack_integration.py` - Test script
- `test_enhanced_rag_slack.py` - Test enhanced RAG with Slack integration

### 2. Test the Integration

```bash
cd src
python test_slack_integration.py
```

### 3. Basic Usage

```python
from services.slack_notification_service import send_matches_to_slack

# After getting matches from RAG service
matches, metadata = await rag_service.enhanced_search(query)

# Send to Slack
await send_matches_to_slack(matches, query, metadata)
```

## 📋 Integration Points

### Option 1: Direct Integration (Recommended)

Add this to any file where you have matches:

```python
from services.slack_notification_service import send_matches_to_slack

# After your existing search logic
matches, metadata = await rag_service.enhanced_search(query)

# Send to Slack (non-blocking)
asyncio.create_task(send_matches_to_slack(matches, query, metadata))
```

### Option 2: Chat Controller Integration

Add to `chat_controller.py` after line 79 where you have matches:

```python
# Add this import at the top
from services.slack_notification_service import send_matches_to_slack

# Add this after getting matches (around line 79)
# Send to Slack asynchronously
asyncio.create_task(send_matches_to_slack(matches, request.message, search_metadata))
```

### Option 3: Enhanced RAG Integration (✅ IMPLEMENTED)

**Automatic integration after final ranking:**

The Enhanced RAG service now automatically sends Slack notifications after final ranking is complete. Simply use the service as normal:

```python
from services.enhanced_rag_service import enhanced_rag_service

# Search with automatic Slack notification after final ranking (default)
matches, metadata = await enhanced_rag_service.intelligent_search(
    query="Find Python developers",
    top_k=10,
    enable_slack_notification=True  # Default: True
)

# Search without Slack notification
matches, metadata = await enhanced_rag_service.intelligent_search(
    query="Find Python developers",
    enable_slack_notification=False
)
```

**What happens automatically:**

1. Enhanced query analysis
2. Multi-faceted search with variations
3. Intelligent re-ranking of results
4. 🚀 **Slack notification sent after final ranking**

**Test the integration:**

```bash
cd src
python test_enhanced_rag_slack.py
```

## 🔧 Configuration

### Slack Token

Your token is already configured in the service:
`xoxb-9339590015462-9339599690838-UKKdPG6yiEjcagGiJ44mk1FP`

### Channel

Default channel: `#test_message`

To change channel:

```python
await send_matches_to_slack(matches, query, metadata, channel="#your-channel")
```

## 📱 Message Format

The Slack message includes:

- 🎯 Search query and timestamp
- 📊 Total matches found
- 🔧 Detected skills and requirements
- 📋 Top candidates with:
  - Name and match percentage
  - File name
  - Key skills
  - Experience summary
  - Text preview

## 🛠️ Advanced Usage

### Send Only Summary

```python
from services.slack_notification_service import slack_notification_service

await slack_notification_service.send_search_summary(
    search_query=query,
    total_results=len(matches),
    search_metadata=metadata
)
```

### Send with Raw JSON

```python
await slack_notification_service.send_json_data(
    matches=matches,
    search_query=query,
    include_raw_json=True  # Includes JSON data block
)
```

### Custom Messages

```python
custom_msg = "🎯 Custom notification about search results"
await slack_notification_service.send_custom_message(custom_msg)
```

## 🔍 No Code Changes Required

This integration is designed to work alongside your existing code without modifications. You can:

1. Keep using your existing RAG service as-is
2. Add Slack notifications wherever you have matches
3. Test independently with the test script

## 🐛 Troubleshooting

### Message Not Sent

- Check Slack token permissions
- Verify channel exists and bot has access
- Check internet connection

### Test Connection

```bash
python test_slack_integration.py
```

### Debug Mode

Enable logging to see detailed error messages:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## 📝 Examples

See `slack_integration_example.py` for complete usage examples and integration patterns.

## 🎯 Perfect for Your Use Case

This setup is ideal because:

- ✅ No existing code changes needed
- ✅ Works with your current JSON output format
- ✅ Sends after vector DB retrieval is complete
- ✅ Formatted specifically for resume data
- ✅ Handles your search metadata
- ✅ Easy to integrate anywhere in your codebase
