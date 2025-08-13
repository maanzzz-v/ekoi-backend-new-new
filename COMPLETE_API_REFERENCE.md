# Complete API Documentation for Frontend Integration

## Base URL

```
http://localhost:8000
```

---

## 🏥 HEALTH & STATUS ENDPOINTS

### 1. Basic Health Check

**Endpoint:** `GET /api/v1/health/`

**Purpose:** Check if the API is running

**Input:** None

**Output:**

```json
{
  "status": "healthy",
  "app_name": "ekoi-backend",
  "version": "0.1.0"
}
```

**HTTP Status:** 200

---

### 2. Detailed Health Check

**Endpoint:** `GET /api/v1/health/detailed`

**Purpose:** Check status of all system components (database, vector DB, LLM)

**Input:** None

**Output:**

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

**HTTP Status:** 200 (healthy) | 503 (unhealthy)

---

### 3. LLM Provider Information

**Endpoint:** `GET /api/v1/health/llm-provider`

**Purpose:** Get current LLM provider configuration

**Input:** None

**Output:**

```json
{
  "status": "success",
  "provider_info": {
    "provider": "openai",
    "dimension": 1536,
    "model": "text-embedding-ada-002"
  },
  "available_providers": [
    "sentence-transformers",
    "openai",
    "gemini",
    "ollama",
    "vllm"
  ]
}
```

**HTTP Status:** 200

---

## 📄 RESUME MANAGEMENT ENDPOINTS

### 4. Upload Resumes

**Endpoint:** `POST /api/v1/resumes/upload`

**Purpose:** Upload one or multiple resume files for processing

**Content-Type:** `multipart/form-data`

**Input:**

```javascript
// Form data with files
const formData = new FormData();
formData.append("files", file1); // PDF, DOCX, TXT
formData.append("files", file2);
formData.append("files", file3);
```

**Output (Success):**

```json
{
  "message": "Successfully processed 3 out of 3 files",
  "uploaded_files": [
    "john_doe_resume.pdf",
    "jane_smith_cv.docx",
    "alex_johnson.txt"
  ],
  "total_files": 3,
  "success": true
}
```

**Output (Partial Success):**

```json
{
  "message": "Successfully processed 2 out of 3 files",
  "uploaded_files": ["file1.pdf", "file2.docx"],
  "failed_files": ["corrupted_file.pdf"],
  "errors": ["File corrupted_file.pdf is corrupted"],
  "total_files": 3,
  "success": false
}
```

**HTTP Status:** 200 (success) | 400 (validation error) | 413 (file too large)

**Supported File Types:** PDF, DOCX, TXT
**Max File Size:** 10MB per file

---

### 5. List All Resumes

**Endpoint:** `GET /api/v1/resumes/`

**Purpose:** Get paginated list of all uploaded resumes

**Query Parameters:**

- `skip`: Number of resumes to skip (default: 0)
- `limit`: Maximum resumes to return (1-100, default: 50)

**Example Request:**

```
GET /api/v1/resumes/?skip=0&limit=10
```

**Output:**

```json
{
  "resumes": [
    {
      "id": "689c2f13af846c8f01d65389",
      "file_name": "john_doe_resume.pdf",
      "file_type": "pdf",
      "file_size": 2456,
      "file_path": "/home/user/resumes/20250813_062211_john_doe_resume.pdf",
      "upload_timestamp": "2025-08-13T06:22:11.489000",
      "processed": true,
      "processing_timestamp": "2025-08-13T06:22:21.316000",
      "extracted_info": {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "(555) 123-4567",
        "skills": [
          "Python",
          "JavaScript",
          "AWS",
          "Django",
          "React",
          "Node.js",
          "Docker",
          "Kubernetes",
          "PostgreSQL"
        ],
        "experience": [
          {
            "description": "Senior Software Engineer | Tech Solutions Inc. | 2021 - Present",
            "extracted": true
          },
          {
            "description": "Software Engineer | Digital Innovations | 2019 - 2021",
            "extracted": true
          }
        ],
        "education": [
          {
            "description": "Bachelor of Science in Computer Science | State University | 2015 - 2019",
            "extracted": true
          }
        ],
        "summary": "Experienced Software Engineer with 5+ years of experience in full-stack development, specializing in Python, JavaScript, and cloud technologies."
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

**HTTP Status:** 200

---

### 6. Download Resume File

**Endpoint:** `GET /api/v1/resumes/{resume_id}/download`

**Purpose:** Download the original resume file

**Path Parameters:**

- `resume_id`: The resume ID from the list endpoint

**Example Request:**

```
GET /api/v1/resumes/689c2f13af846c8f01d65389/download
```

**Output:** Binary file content (PDF/DOCX/TXT)

**Headers:**

```
Content-Type: application/pdf | application/vnd.openxmlformats-officedocument.wordprocessingml.document | text/plain
Content-Disposition: attachment; filename="john_doe_resume.pdf"
```

**HTTP Status:** 200 (success) | 404 (resume not found)

---

### 7. Delete Resume

**Endpoint:** `DELETE /api/v1/resumes/{resume_id}`

**Purpose:** Delete a resume and its associated data

**Path Parameters:**

- `resume_id`: The resume ID to delete

**Example Request:**

```
DELETE /api/v1/resumes/689c2f13af846c8f01d65389
```

**Output:**

```json
{
  "message": "Resume deleted successfully",
  "success": true
}
```

**HTTP Status:** 200 (success) | 404 (resume not found)

---

## 🔍 SEARCH ENDPOINTS

### 8. Basic Resume Search

**Endpoint:** `POST /api/v1/resumes/search`

**Purpose:** Search resumes using keywords and filters

**Content-Type:** `application/json`

**Input:**

```json
{
  "query": "Python developer with AWS experience",
  "limit": 10,
  "filters": {
    "min_experience_years": 3,
    "skills": ["Python", "AWS"],
    "location": "San Francisco"
  }
}
```

**Required Fields:**

- `query`: Search string

**Optional Fields:**

- `limit`: Number of results (1-50, default: 10)
- `filters`: Additional filters (optional)

**Output:**

```json
{
  "query": "Python developer with AWS experience",
  "total_results": 3,
  "matches": [
    {
      "id": "689c2f13af846c8f01d65389",
      "file_name": "john_doe_resume.pdf",
      "score": 0.892,
      "extracted_info": {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "(555) 123-4567",
        "skills": ["Python", "AWS", "Django", "React"],
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
      "relevant_text": "Experienced Python developer with 5+ years of experience in full-stack development, specializing in Python, JavaScript, and cloud technologies including AWS..."
    }
  ],
  "processing_time": 2.34,
  "success": true
}
```

**HTTP Status:** 200 (success) | 422 (validation error)

---

### 9. Conversational Search (Standalone)

**Endpoint:** `POST /api/v1/chat/search`

**Purpose:** Natural language resume search without session context

**Content-Type:** `application/json`

**Input:**

```json
{
  "message": "Find me senior Python developers who have worked with startups and know React",
  "top_k": 5,
  "filters": {}
}
```

**Required Fields:**

- `message`: Natural language search query

**Optional Fields:**

- `top_k`: Number of results (1-50, default: 10)
- `filters`: Additional filters (optional)

**Output:**

```json
{
  "message": "I found 3 resumes showing excellent alignment with your requirements. These candidates have strong Python experience and startup backgrounds. The top candidate has 6+ years of Python development with React expertise at 2 different startups.",
  "query": "senior Python developers startup React python py senior lead startup startup experience react javascript",
  "original_message": "Find me senior Python developers who have worked with startups and know React",
  "matches": [
    {
      "id": "689c2f13af846c8f01d65389",
      "file_name": "john_doe_resume.pdf",
      "score": 0.945,
      "extracted_info": { ... },
      "relevant_text": "Senior Python developer with 6+ years experience..."
    }
  ],
  "total_results": 3,
  "success": true,
  "session_id": null
}
```

**HTTP Status:** 200 (success) | 422 (validation error)

---

## 💬 CHAT SESSION MANAGEMENT

### 10. Create New Chat Session

**Endpoint:** `POST /api/v1/chat/sessions`

**Purpose:** Create a new conversation session for recruitment

**Content-Type:** `application/json`

**Input:**

```json
{
  "title": "Python Developer Search",
  "initial_message": "I need to find experienced Python developers for a fintech startup"
}
```

**Optional Fields:**

- `title`: Session title (auto-generated if not provided)
- `initial_message`: First message in the session

**Output:**

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
        "content": "I need to find experienced Python developers for a fintech startup",
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

**HTTP Status:** 200 (success) | 500 (server error)

---

### 11. List All Chat Sessions

**Endpoint:** `GET /api/v1/chat/sessions`

**Purpose:** Get list of all chat sessions with pagination

**Query Parameters:**

- `limit`: Maximum sessions to return (1-100, default: 50)
- `skip`: Number of sessions to skip (default: 0)
- `active_only`: Only active sessions (default: true)

**Example Request:**

```
GET /api/v1/chat/sessions?limit=20&skip=0&active_only=true
```

**Output:**

```json
{
  "sessions": [
    {
      "id": "2f821f70-1026-4779-ab89-8297af2e9993",
      "title": "Python Developer Search",
      "created_at": "2025-08-13T06:39:05.412000",
      "updated_at": "2025-08-13T06:42:24.702000",
      "messages": [
        {
          "id": "d7fce930-ad6d-40e1-8b09-004e7fcd57aa",
          "type": "user",
          "content": "I need to find experienced Python developers",
          "timestamp": "2025-08-13T06:39:05.412000",
          "metadata": null
        },
        {
          "id": "ca3243b8-44ca-44c9-811b-6137335f97c0",
          "type": "assistant",
          "content": "I found 3 Python developers matching your criteria...",
          "timestamp": "2025-08-13T06:39:37.331000",
          "metadata": {
            "search_results": ["689c2f13af846c8f01d65389"],
            "search_metadata": { ... }
          }
        }
      ],
      "context": {
        "last_search": {
          "query": "Python developers",
          "results": ["689c2f13af846c8f01d65389"],
          "total_results": 3
        }
      },
      "is_active": true
    }
  ],
  "total": 5,
  "success": true
}
```

**HTTP Status:** 200

---

### 12. Get Specific Chat Session

**Endpoint:** `GET /api/v1/chat/sessions/{session_id}`

**Purpose:** Retrieve complete details of a specific session

**Path Parameters:**

- `session_id`: The session ID

**Example Request:**

```
GET /api/v1/chat/sessions/2f821f70-1026-4779-ab89-8297af2e9993
```

**Output:**

```json
{
  "session": {
    "id": "2f821f70-1026-4779-ab89-8297af2e9993",
    "title": "Python Developer Search",
    "created_at": "2025-08-13T06:39:05.412000",
    "updated_at": "2025-08-13T06:42:24.702000",
    "messages": [
      {
        "id": "msg1",
        "type": "user",
        "content": "Find Python developers with Django experience",
        "timestamp": "2025-08-13T06:39:05.412000",
        "metadata": null
      },
      {
        "id": "msg2",
        "type": "assistant",
        "content": "I found 2 candidates with strong Python and Django backgrounds...",
        "timestamp": "2025-08-13T06:39:15.123000",
        "metadata": {
          "search_results": ["resume_id_1", "resume_id_2"],
          "search_metadata": { ... }
        }
      }
    ],
    "context": {
      "last_search": {
        "query": "Python developers Django",
        "results": ["resume_id_1", "resume_id_2"],
        "total_results": 2
      }
    },
    "is_active": true
  },
  "success": true,
  "message": "Session retrieved successfully"
}
```

**HTTP Status:** 200 (success) | 404 (session not found)

---

### 13. Search Within Session

**Endpoint:** `POST /api/v1/chat/sessions/{session_id}/search`

**Purpose:** Perform resume search within session context

**Path Parameters:**

- `session_id`: The session ID

**Content-Type:** `application/json`

**Input:**

```json
{
  "message": "Find Python developers with Django and AWS experience",
  "top_k": 5,
  "filters": {}
}
```

**Required Fields:**

- `message`: Natural language search query

**Optional Fields:**

- `top_k`: Number of results (1-50, default: 10)
- `filters`: Additional filters

**Output:**

```json
{
  "message": "I found 2 excellent candidates matching your Django and AWS requirements. Both have 4+ years of Python experience with production Django applications and cloud deployment experience.",
  "query": "Python developers Django AWS python django aws cloud deployment",
  "original_message": "Find Python developers with Django and AWS experience",
  "matches": [
    {
      "id": "689c2f13af846c8f01d65389",
      "file_name": "john_doe_resume.pdf",
      "score": 0.932,
      "extracted_info": {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "skills": ["Python", "Django", "AWS", "PostgreSQL"],
        "experience": [
          {
            "description": "Senior Software Engineer | Tech Solutions Inc. | 2021 - Present",
            "extracted": true
          }
        ],
        "summary": "Python developer with Django and AWS experience..."
      },
      "relevant_text": "Experienced Python developer specializing in Django web applications..."
    }
  ],
  "total_results": 2,
  "success": true,
  "session_id": "2f821f70-1026-4779-ab89-8297af2e9993"
}
```

**HTTP Status:** 200 (success) | 404 (session not found) | 422 (validation error)

---

### 14. Ask Follow-up Questions

**Endpoint:** `POST /api/v1/chat/sessions/{session_id}/followup`

**Purpose:** Ask intelligent follow-up questions about search results

**Path Parameters:**

- `session_id`: The session ID

**Content-Type:** `application/json`

**Input:**

```json
{
  "question": "Why was John Doe selected? What are his key strengths?",
  "previous_search_results": ["689c2f13af846c8f01d65389"]
}
```

**Required Fields:**

- `question`: The follow-up question

**Optional Fields:**

- `previous_search_results`: List of resume IDs to analyze

**Common Follow-up Questions:**

- "Why were these candidates selected?"
- "What are the key strengths of the top candidate?"
- "How do these candidates compare in terms of experience?"
- "Which candidate would be best for a startup environment?"
- "What technical skills do they have in common?"
- "Who has the most relevant cloud experience?"
- "Compare their educational backgrounds"
- "Which candidate has leadership experience?"

**Output:**

```json
{
  "session_id": "2f821f70-1026-4779-ab89-8297af2e9993",
  "question": "Why was John Doe selected? What are his key strengths?",
  "answer": "John Doe was selected because of his exceptional combination of technical skills and experience:\n\n**Key Strengths:**\n1. **Strong Python Expertise**: 5+ years of professional Python development\n2. **Django Mastery**: Extensive experience building scalable web applications\n3. **Cloud Proficiency**: Proven AWS experience with EC2, S3, and Lambda\n4. **Leadership Experience**: Led a team of 4 developers at Tech Solutions Inc.\n5. **Full-Stack Capabilities**: Comfortable with both backend and frontend technologies\n6. **Startup Experience**: Has worked in fast-paced startup environments\n\n**Why He Stands Out:**\n- His resume shows progression from junior to senior roles\n- Strong educational background in Computer Science\n- Combination of technical depth and breadth\n- Experience with modern development practices (CI/CD, Docker)",
  "success": true
}
```

**HTTP Status:** 200 (success) | 404 (session not found)

---

### 15. Delete Chat Session

**Endpoint:** `DELETE /api/v1/chat/sessions/{session_id}`

**Purpose:** Delete (deactivate) a chat session

**Path Parameters:**

- `session_id`: The session ID to delete

**Example Request:**

```
DELETE /api/v1/chat/sessions/2f821f70-1026-4779-ab89-8297af2e9993
```

**Output:**

```json
{
  "session_id": "2f821f70-1026-4779-ab89-8297af2e9993",
  "message": "Session deleted successfully",
  "success": true
}
```

**HTTP Status:** 200 (success) | 404 (session not found)

---

## 🏠 ROOT ENDPOINT

### 16. API Root

**Endpoint:** `GET /`

**Purpose:** API welcome message and navigation

**Input:** None

**Output:**

```json
{
  "message": "Welcome to Resume Indexer API",
  "version": "0.1.0",
  "docs": "/docs",
  "health": "/api/v1/health"
}
```

**HTTP Status:** 200

---

## 🚨 ERROR RESPONSES

All endpoints return consistent error formats:

### Validation Error (422)

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "message"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

### Not Found Error (404)

```json
{
  "error": "Resume not found",
  "details": {},
  "success": false
}
```

### Server Error (500)

```json
{
  "error": "Internal server error occurred",
  "details": {},
  "success": false
}
```

---

## 🔧 FRONTEND INTEGRATION EXAMPLES

### JavaScript/React Examples

#### Upload Files

```javascript
const uploadResumes = async (files) => {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));

  const response = await fetch("/api/v1/resumes/upload", {
    method: "POST",
    body: formData,
  });

  return await response.json();
};
```

#### Create Session and Search

```javascript
const createSessionAndSearch = async (title, searchQuery) => {
  // Create session
  const sessionResponse = await fetch("/api/v1/chat/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });

  const session = await sessionResponse.json();

  // Search within session
  const searchResponse = await fetch(
    `/api/v1/chat/sessions/${session.session.id}/search`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: searchQuery, top_k: 10 }),
    }
  );

  return await searchResponse.json();
};
```

#### Ask Follow-up Question

```javascript
const askFollowUp = async (sessionId, question) => {
  const response = await fetch(`/api/v1/chat/sessions/${sessionId}/followup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

  return await response.json();
};
```

---

## 📱 RECOMMENDED UI FLOW

1. **Dashboard**: Show health status, recent uploads, active sessions
2. **Upload Page**: Drag-and-drop file upload with progress
3. **Resume List**: Paginated table with download/delete options
4. **Chat Interface**:
   - Session list sidebar
   - Chat messages with search results
   - Follow-up question buttons
   - Session management (create/delete)
5. **Search Page**: Standalone search for quick queries

This comprehensive API provides everything needed for a complete AI-powered recruitment assistant interface!
