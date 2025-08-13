# Resume Indexer API Documentation

## Complete API Endpoints for Frontend Integration

This document provides comprehensive details for all API endpoints to integrate with your UI application.

---

## 🏥 Health & Status Endpoints

### 1. Basic Health Check

```http
GET /api/v1/health/
```

**Response:**

```json
{
  "status": "healthy",
  "app_name": "ekoi-backend",
  "version": "0.1.0"
}
```

### 2. Detailed Health Check

```http
GET /api/v1/health/detailed
```

**Response:**

```json
{
  "status": "healthy",
  "app_name": "ekoi-backend",
  "version": "0.1.0",
  "components": {
    "database": {
      "status": "healthy",
      "type": "MongoDB"
    },
    "vector_db": {
      "status": "healthy",
      "llm_provider": {
        "provider": "openai",
        "dimension": 1536,
        "model": "text-embedding-ada-002"
      },
      "pinecone_available": true,
      "faiss_available": true
    }
  }
}
```

---

## 📄 Resume Management Endpoints

### 3. Upload Resumes

```http
POST /api/v1/resumes/upload
Content-Type: multipart/form-data
```

**Request Body:**

```form-data
files: [File1.pdf, File2.docx, File3.txt]  // Multiple files supported
```

**Response:**

```json
{
  "message": "Successfully processed 2 out of 2 files",
  "uploaded_files": ["resume1.pdf", "resume2.docx"],
  "total_files": 2,
  "success": true
}
```

### 4. List All Resumes

```http
GET /api/v1/resumes/?skip=0&limit=10
```

**Query Parameters:**

- `skip`: Number of resumes to skip (pagination)
- `limit`: Maximum number of resumes to return (1-100)

**Response:**

```json
{
  "resumes": [
    {
      "id": "689c2f13af846c8f01d65389",
      "file_name": "john_doe_resume.pdf",
      "file_type": "pdf",
      "file_size": 2456,
      "file_path": "/path/to/stored/file.pdf",
      "upload_timestamp": "2025-08-13T06:22:11.489000",
      "processed": true,
      "processing_timestamp": "2025-08-13T06:22:21.316000",
      "extracted_info": {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "(555) 123-4567",
        "skills": ["Python", "JavaScript", "AWS", "Django"],
        "experience": [
          {
            "description": "Senior Software Engineer | Tech Solutions Inc. | 2021 - Present",
            "extracted": true
          }
        ],
        "education": [
          {
            "description": "Bachelor of Science in Computer Science | State University | 2015 - 2019",
            "extracted": true
          }
        ],
        "summary": "Experienced Software Engineer with 5+ years..."
      },
      "has_vectors": true,
      "vector_count": 4
    }
  ],
  "pagination": {
    "total": 25,
    "skip": 0,
    "limit": 10,
    "current_page": 1,
    "total_pages": 3,
    "has_next": true,
    "has_previous": false
  },
  "summary": {
    "total_resumes": 25,
    "showing": 10,
    "processed": 22,
    "unprocessed": 3
  }
}
```

### 5. Download Resume

```http
GET /api/v1/resumes/{resume_id}/download
```

**Response:** File download (PDF, DOCX, or TXT)

### 6. Delete Resume

```http
DELETE /api/v1/resumes/{resume_id}
```

**Response:**

```json
{
  "message": "Resume deleted successfully",
  "success": true
}
```

---

## 🔍 Search Endpoints

### 7. Basic Resume Search

```http
POST /api/v1/resumes/search
Content-Type: application/json
```

**Request Body:**

```json
{
  "query": "Python developer with AWS experience",
  "limit": 10,
  "filters": {
    "min_experience_years": 3,
    "skills": ["Python", "AWS"]
  }
}
```

**Response:**

```json
{
  "query": "Python developer with AWS experience",
  "total_results": 3,
  "matches": [
    {
      "id": "689c2f13af846c8f01d65389",
      "file_name": "john_doe.pdf",
      "score": 0.89,
      "extracted_info": { ... },
      "relevant_text": "Experienced Python developer with 5+ years..."
    }
  ],
  "processing_time": 2.34,
  "success": true
}
```

### 8. Conversational Search (Standalone)

```http
POST /api/v1/chat/search
Content-Type: application/json
```

**Request Body:**

```json
{
  "message": "Find me senior Python developers who have worked with startups",
  "top_k": 5,
  "filters": {}
}
```

**Response:**

```json
{
  "message": "I found 3 resumes matching your criteria. These candidates have strong Python experience...",
  "query": "senior Python developers startup experience python py senior lead",
  "original_message": "Find me senior Python developers who have worked with startups",
  "matches": [ ... ],
  "total_results": 3,
  "success": true,
  "session_id": null
}
```

---

## 💬 Chat Session Management

### 9. Create New Chat Session

```http
POST /api/v1/chat/sessions
Content-Type: application/json
```

**Request Body:**

```json
{
  "title": "Python Developer Search", // Optional
  "initial_message": "I need to find experienced Python developers" // Optional
}
```

**Response:**

```json
{
  "session": {
    "id": "2f821f70-1026-4779-ab89-8297af2e9993",
    "title": "Python Developer Search",
    "created_at": "2025-08-13T06:39:05.412273",
    "updated_at": "2025-08-13T06:39:05.412281",
    "messages": [
      {
        "id": "d7fce930-ad6d-40e1-8b09-004e7fcd57aa",
        "type": "user",
        "content": "I need to find experienced Python developers",
        "timestamp": "2025-08-13T06:39:05.412324",
        "metadata": null
      }
    ],
    "context": {},
    "is_active": true
  },
  "success": true,
  "message": "Session 'Python Developer Search' created successfully"
}
```

### 10. List All Chat Sessions

```http
GET /api/v1/chat/sessions?limit=50&skip=0&active_only=true
```

**Query Parameters:**

- `limit`: Maximum sessions to return (1-100)
- `skip`: Number of sessions to skip
- `active_only`: Only return active sessions (default: true)

**Response:**

```json
{
  "sessions": [
    {
      "id": "2f821f70-1026-4779-ab89-8297af2e9993",
      "title": "Python Developer Search",
      "created_at": "2025-08-13T06:39:05.412000",
      "updated_at": "2025-08-13T06:42:24.702000",
      "messages": [ ... ],
      "context": { ... },
      "is_active": true
    }
  ],
  "total": 5,
  "success": true
}
```

### 11. Get Specific Chat Session

```http
GET /api/v1/chat/sessions/{session_id}
```

**Response:**

```json
{
  "session": {
    "id": "2f821f70-1026-4779-ab89-8297af2e9993",
    "title": "Python Developer Search",
    "messages": [
      {
        "id": "msg1",
        "type": "user",
        "content": "Find Python developers",
        "timestamp": "2025-08-13T06:39:05.412000"
      },
      {
        "id": "msg2",
        "type": "assistant",
        "content": "I found 3 Python developers...",
        "timestamp": "2025-08-13T06:39:15.123000",
        "metadata": {
          "search_results": ["resume_id_1", "resume_id_2"]
        }
      }
    ],
    "context": {
      "last_search": {
        "query": "Python developers",
        "results": ["resume_id_1", "resume_id_2"],
        "total_results": 2
      }
    }
  },
  "success": true,
  "message": "Session retrieved successfully"
}
```

### 12. Search Within Session

```http
POST /api/v1/chat/sessions/{session_id}/search
Content-Type: application/json
```

**Request Body:**

```json
{
  "message": "Find Python developers with Django and AWS experience",
  "top_k": 5
}
```

**Response:**

```json
{
  "message": "I found 2 candidates matching your requirements...",
  "query": "Python developers Django AWS python django aws cloud",
  "original_message": "Find Python developers with Django and AWS experience",
  "matches": [ ... ],
  "total_results": 2,
  "success": true,
  "session_id": "2f821f70-1026-4779-ab89-8297af2e9993"
}
```

### 13. Ask Follow-up Questions

```http
POST /api/v1/chat/sessions/{session_id}/followup
Content-Type: application/json
```

**Request Body:**

```json
{
  "question": "Why was John Doe selected? What are his key strengths?",
  "previous_search_results": ["resume_id_1", "resume_id_2"] // Optional
}
```

**Response:**

```json
{
  "session_id": "2f821f70-1026-4779-ab89-8297af2e9993",
  "question": "Why was John Doe selected? What are his key strengths?",
  "answer": "John Doe was selected because of his strong Python expertise, 5+ years of experience with Django, and proven AWS cloud experience. His key strengths include: 1) Full-stack development capabilities, 2) Cloud architecture experience, 3) Leadership experience as a Senior Engineer.",
  "success": true
}
```

**Common Follow-up Questions:**

- "Why were these candidates selected?"
- "What are the key strengths of the top candidate?"
- "How do these candidates compare in terms of experience?"
- "Which candidate would be best for a startup environment?"
- "What technical skills do they have in common?"
- "Who has the most relevant experience?"

### 14. Delete Chat Session

```http
DELETE /api/v1/chat/sessions/{session_id}
```

**Response:**

```json
{
  "session_id": "2f821f70-1026-4779-ab89-8297af2e9993",
  "message": "Session deleted successfully",
  "success": true
}
```

---

## 🚀 Typical UI Integration Flow

### For Resume Upload Page:

1. Use endpoint #3 to upload files
2. Use endpoint #4 to display uploaded resumes
3. Use endpoint #5 for file downloads
4. Use endpoint #6 for deletions

### For Chat Interface:

1. **Create Session**: Use endpoint #9 when user starts new conversation
2. **Load Sessions**: Use endpoint #10 to show previous conversations
3. **Resume Session**: Use endpoint #11 to load specific session
4. **Search**: Use endpoint #12 for resume searches within session
5. **Follow-up**: Use endpoint #13 for follow-up questions
6. **Delete**: Use endpoint #14 to remove old sessions

### For Search Page:

1. Use endpoint #7 for basic search
2. Use endpoint #8 for conversational search without sessions

---

## 📊 Response Codes

- **200**: Success
- **404**: Resource not found (session, resume)
- **422**: Validation error (invalid request body)
- **500**: Server error

---

## 🔧 Error Handling

All endpoints return errors in this format:

```json
{
  "error": "Error description",
  "details": {},
  "success": false
}
```

---

## 💡 Implementation Tips

1. **Session Management**: Create a new session for each recruitment task
2. **Pagination**: Use `skip` and `limit` for large datasets
3. **Follow-ups**: Store previous search results to enable intelligent follow-up questions
4. **Real-time**: Consider WebSocket integration for real-time search updates
5. **File Upload**: Support drag-and-drop for multiple file uploads
6. **Search Suggestions**: Use the conversational responses to guide users

This API provides a complete solution for AI-powered resume search and management with session-based conversations and intelligent follow-up capabilities!
