# Complete API Documentation for Frontend Integration

## Base URL

```
http://localhost:8000
```

## 🔥 ENHANCED FEATURES OVERVIEW

**NEW ENHANCEMENTS:**

- 🧠 **Intelligent Query Understanding**: Advanced AI-powered query analysis and intent detection
- 🎨 **UI-Optimized Responses**: Structured data perfect for frontend components
- 🔄 **Conversation Flow Management**: Smart follow-up suggestions and quick actions
- 📊 **Real-time Analytics**: Search insights, quality indicators, and performance metrics
- 🎯 **Context-Aware Sessions**: Persistent conversations with memory and context
- ⚡ **Response Optimization**: Clean, structured responses for seamless UI integration

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

## 🔍 ENHANCED SEARCH ENDPOINTS

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

### 9. 🚀 Intelligent Chat Search (Enhanced)

**Endpoint:** `POST /api/v1/chat/search`

**Purpose:** AI-powered natural language resume search with UI-optimized responses

**Content-Type:** `application/json`

**Input:**

```json
{
  "message": "Find senior Python developers with AWS experience for a startup",
  "top_k": 5,
  "filters": {}
}
```

**Required Fields:**

- `message`: Natural language search query

**Optional Fields:**

- `top_k`: Number of results (1-50, default: 10)
- `filters`: Additional filters (optional)

**Enhanced Output:**

```json
{
  "message": "🎯 ••Found 1 skilled candidate•• 🔧 ••Common skills••: Javascript, Aws, Flask, Kubernetes, C++",
  "query": "Find Python developers with AWS experience for a startup python py django aws amazon web services ec2",
  "original_message": "Find senior Python developers with AWS experience for a startup",
  "matches": [
    {
      "id": "689c2f13af846c8f01d65389",
      "file_name": "test_resume.txt",
      "score": 1.1078790963939393,
      "extracted_info": {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": null,
        "skills": [
          "Javascript",
          "Aws",
          "Flask",
          "Kubernetes",
          "C++",
          "Docker",
          "Postgresql",
          "Jenkins",
          "Ci/Cd",
          "Agile",
          "Git",
          "Django",
          "Sql",
          "Mongodb",
          "Redis",
          "Java",
          "Python",
          "Node.Js",
          "Terraform",
          "React",
          "Azure"
        ],
        "experience": [
          {
            "description": "Senior Software Engineer | Tech Solutions Inc. | 2021 - Present",
            "extracted": true
          }
        ],
        "summary": "Experienced Software Engineer with 5+ years of experience in full-stack development, specializing in Python, JavaScript, and cloud technologies."
      },
      "relevant_text": "John Doe\nEmail: john.doe@example.com\nPhone: (555) 123-4567..."
    }
  ],
  "total_results": 1,
  "success": true,
  "session_id": null,

  // 🎨 NEW: UI-Optimized Components
  "ui_components": {
    "candidate_cards": [
      {
        "id": "689c2f13af846c8f01d65389",
        "rank": 1,
        "score": 1.108,
        "name": "John Doe",
        "title": "Candidate",
        "skills": [
          "Javascript",
          "Aws",
          "Flask",
          "Kubernetes",
          "C++",
          "Docker",
          "Postgresql",
          "Jenkins"
        ],
        "experience_summary": "3 roles listed",
        "match_highlights": [
          "Experienced Software Engineer with 5+ years of experience..."
        ],
        "file_name": "test_resume.txt"
      }
    ],
    "skill_tags": ["Flask", "Aws", "Javascript", "C++", "Kubernetes"],
    "experience_chart": {
      "Junior": 0,
      "Mid-level": 1,
      "Senior": 0,
      "Lead": 0
    },
    "quality_indicators": {
      "total_matches": 1,
      "high_quality": 0,
      "average_score": 1.03,
      "consistency": 1.0
    },
    "search_insights": {
      "detected_domains": ["data", "cloud", "backend"],
      "technical_depth": "medium",
      "intent_confidence": 0.8
    }
  },

  // 🔄 NEW: Conversation Flow Management
  "conversation_flow": {
    "next_suggestions": [],
    "follow_up_questions": [
      "Why is John Doe the best match?",
      "Compare the technical skills of these candidates",
      "Who has the most relevant experience?",
      "Which candidate would fit best in a startup environment?"
    ],
    "refinement_options": [
      "Broaden the search criteria",
      "Consider related technologies",
      "Include junior-level candidates"
    ],
    "flow_type": "search_results"
  },

  // ⚡ NEW: Quick Actions for UI
  "quick_actions": [
    {
      "label": "📧 Contact top candidate",
      "action": "contact",
      "target": "689c2f13af846c8f01d65389"
    },
    {
      "label": "📋 Compare all candidates",
      "action": "compare",
      "query": "Compare these candidates in detail"
    },
    {
      "label": "🔍 Refine search",
      "action": "refine",
      "query": ""
    },
    {
      "label": "Find more Flask experts",
      "action": "search",
      "query": "Find candidates with Flask expertise"
    }
  ],

  // 📊 NEW: Response Metadata
  "response_metadata": {
    "response_type": "single_match",
    "confidence_level": "medium",
    "search_quality": {
      "average_score": 1.026485157,
      "score_distribution": {
        "excellent": 1,
        "good": 0,
        "fair": 0,
        "poor": 0
      },
      "top_score": 1.026485157,
      "consistency": 1.0
    },
    "timestamp": "2025-08-13T07:38:48.301120"
  }
}
```

**🎯 Key Enhancements:**

- **UI Components**: Ready-to-use candidate cards, skill tags, charts
- **Conversation Flow**: Smart follow-up suggestions and refinement options
- **Quick Actions**: Interactive buttons for user engagement
- **Search Insights**: AI analysis of query intent and technical depth
- **Quality Indicators**: Match quality metrics and consistency scores

**HTTP Status:** 200 (success) | 422 (validation error)

---

### 10. 🧠 Query Analysis (NEW)

**Endpoint:** `POST /api/v1/chat/analyze?message={query}`

**Purpose:** Analyze user queries for intent, skills, and optimization suggestions

**Query Parameters:**

- `message`: The query to analyze (URL encoded)

**Example Request:**

```
POST /api/v1/chat/analyze?message=Find%20senior%20React%20developers%20with%205%2B%20years%20experience
```

**Output:**

```json
{
  "original_message": "Find senior React developers with 5+ years experience",
  "intelligence_analysis": {
    "original_query": "Find senior React developers with 5+ years experience",
    "query_type": "skill_search",
    "intent_confidence": 0.8,
    "skill_domains": [
      {
        "domain": "frontend",
        "score": 0.4,
        "description": "Frontend development",
        "matched_skills": ["react"]
      }
    ],
    "experience_indicators": {
      "years_mentioned": 5,
      "level": "senior"
    },
    "role_specificity": "general",
    "urgency_level": "normal",
    "search_scope": "broad",
    "context_aware": false,
    "semantic_keywords": [
      "senior",
      "react",
      "developers",
      "years",
      "experience"
    ],
    "technical_depth": "low",
    "suggestions": ["Add specific technical skills or programming languages"],
    "extracted_keywords": [
      "senior",
      "react",
      "developers",
      "years",
      "experience"
    ]
  },
  "query_quality": {
    "score": 0.8,
    "level": "excellent",
    "completeness": 0.8
  },
  "optimization_tips": [
    "💡 Consider mentioning project context or industry domain",
    "🔍 Add more technical details for better matching"
  ]
}
```

**Use Cases:**

- **Real-time Query Validation**: Show users query quality as they type
- **Search Suggestions**: Provide optimization tips before searching
- **Intent Detection**: Understand what users are really looking for
- **Auto-completion**: Suggest relevant skills and keywords

**HTTP Status:** 200 (success) | 422 (validation error)

---

### 11. 🔧 Query Optimization (NEW)

**Endpoint:** `POST /api/v1/chat/optimize-query?query={query}`

**Purpose:** Get suggestions to improve query quality and search effectiveness

**Query Parameters:**

- `query`: The query to optimize (URL encoded)

**Example Request:**

```
POST /api/v1/chat/optimize-query?query=I%20need%20someone%20good%20with%20computers
```

**Output:**

```json
{
  "original_query": "I need someone good with computers",
  "query_analysis": {
    "intent_type": "skill_search",
    "confidence": 0.8,
    "technical_depth": "low",
    "detected_skills": ["backend"]
  },
  "quality_assessment": {
    "score": 0.65,
    "level": "good",
    "completeness": 0.65
  },
  "optimization_suggestions": [
    "Add specific technical skills or programming languages",
    "Specify experience level (junior, senior, etc.) or years of experience"
  ],
  "optimization_tips": [
    "💡 Consider mentioning project context or industry domain",
    "🔍 Add more technical details for better matching"
  ],
  "enhanced_alternatives": [
    {
      "query": "Find Backend development professionals with i need someone good with computers",
      "improvement": "Added Backend development context",
      "expected_improvement": "More specific results"
    }
  ],
  "success": true
}
```

**Frontend Integration:**

- **Live Query Enhancement**: Show optimization suggestions as users type
- **One-click Improvements**: Buttons to apply suggested enhancements
- **Quality Indicators**: Visual feedback on query effectiveness
- **Alternative Suggestions**: Multiple improved query options

**HTTP Status:** 200 (success) | 422 (validation error)

---

## 💬 ENHANCED CHAT SESSION MANAGEMENT

### 12. Create New Chat Session

**Endpoint:** `POST /api/v1/chat/sessions`

**Purpose:** Create a new conversation session for recruitment

**Content-Type:** `application/json`

**Input:**

```json
{
  "user_id": "user123",
  "name": "Python Developer Search"
}
```

**Optional Fields:**

- `user_id`: User identifier (default: "anonymous")
- `name`: Session name (auto-generated if not provided)

**Output:**

```json
{
  "session": {
    "id": "ce949674-f867-4a1e-b920-87e2a948a339",
    "title": "Resume Search Session 2025-08-13 07:41",
    "created_at": "2025-08-13T07:41:07.152413",
    "updated_at": "2025-08-13T07:41:07.152416",
    "messages": [],
    "context": {},
    "is_active": true
  },
  "success": true,
  "message": "Session 'Resume Search Session 2025-08-13 07:41' created successfully"
}
```

**HTTP Status:** 200 (success) | 500 (server error)

---

### 13. List All Chat Sessions

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
      "id": "ce949674-f867-4a1e-b920-87e2a948a339",
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
            "search_metadata": {}
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

### 14. Get Specific Chat Session

**Endpoint:** `GET /api/v1/chat/sessions/{session_id}`

**Purpose:** Retrieve complete details of a specific session

**Path Parameters:**

- `session_id`: The session ID

**Example Request:**

```
GET /api/v1/chat/sessions/ce949674-f867-4a1e-b920-87e2a948a339
```

**Output:**

```json
{
  "session": {
    "id": "ce949674-f867-4a1e-b920-87e2a948a339",
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
          "search_metadata": {}
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

### 15. 🚀 Enhanced Session Search (With UI Components)

**Endpoint:** `POST /api/v1/chat/sessions/{session_id}/search`

**Purpose:** Perform intelligent resume search within session context with UI optimization

**Path Parameters:**

- `session_id`: The session ID

**Content-Type:** `application/json`

**Input:**

```json
{
  "message": "Tell me about Python developers with backend experience",
  "top_k": 3
}
```

**Required Fields:**

- `message`: Natural language search query

**Optional Fields:**

- `top_k`: Number of results (1-50, default: 10)
- `filters`: Additional filters

**Enhanced Output with UI Components:**

```json
{
  "message": "📈 ••Found 1 candidate matching experience criteria•• 📊 ••Experience breakdown:•• • Mid: 1 candidate",
  "query": "Tell me about Python developers with backend experience python py django",
  "original_message": "Tell me about Python developers with backend experience",
  "matches": [
    {
      "id": "689c2f13af846c8f01d65389",
      "file_name": "test_resume.txt",
      "score": 1.0861821073939393,
      "extracted_info": {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "skills": [
          "Javascript",
          "Aws",
          "Flask",
          "Kubernetes",
          "Python",
          "Django"
        ],
        "experience": [
          {
            "description": "Senior Software Engineer | Tech Solutions Inc. | 2021 - Present",
            "extracted": true
          }
        ],
        "summary": "Experienced Software Engineer with 5+ years of experience in full-stack development, specializing in Python, JavaScript, and cloud technologies."
      },
      "relevant_text": "Experienced Software Engineer with 5+ years of experience in full-stack development, specializing in Python, JavaScript, and cloud technologies..."
    }
  ],
  "total_results": 1,
  "success": true,
  "session_id": "ce949674-f867-4a1e-b920-87e2a948a339",

  // 🎨 UI-Optimized Components (Same as chat/search)
  "ui_components": {
    "candidate_cards": [
      {
        "id": "689c2f13af846c8f01d65389",
        "rank": 1,
        "score": 1.086,
        "name": "John Doe",
        "title": "Candidate",
        "skills": ["Javascript", "Aws", "Flask", "Kubernetes", "C++", "Docker"],
        "experience_summary": "3 roles listed",
        "match_highlights": [
          "Experienced Software Engineer with 5+ years of experience..."
        ],
        "file_name": "test_resume.txt"
      }
    ],
    "skill_tags": ["Flask", "Aws", "Javascript", "C++", "Kubernetes"],
    "experience_chart": {
      "Junior": 0,
      "Mid-level": 1,
      "Senior": 0,
      "Lead": 0
    },
    "quality_indicators": {
      "total_matches": 1,
      "high_quality": 0,
      "average_score": 1.05,
      "consistency": 1.0
    },
    "search_insights": {
      "detected_domains": ["data", "backend"],
      "technical_depth": "low",
      "intent_confidence": 0.7
    }
  },

  // 🔄 Conversation Flow with Session Context
  "conversation_flow": {
    "next_suggestions": [],
    "follow_up_questions": [
      "Why is John Doe the best match?",
      "Compare the technical skills of these candidates",
      "Who has the most relevant experience?",
      "Which candidate would fit best in a startup environment?"
    ],
    "refinement_options": [
      "Broaden the search criteria",
      "Consider related technologies",
      "Include junior-level candidates"
    ],
    "flow_type": "search_results"
  },

  // ⚡ Quick Actions with Session Awareness
  "quick_actions": [
    {
      "label": "📧 Contact top candidate",
      "action": "contact",
      "target": "689c2f13af846c8f01d65389"
    },
    {
      "label": "📋 Compare all candidates",
      "action": "compare",
      "query": "Compare these candidates in detail"
    },
    {
      "label": "🔍 Refine search",
      "action": "refine",
      "query": ""
    },
    {
      "label": "Find more Flask experts",
      "action": "search",
      "query": "Find candidates with Flask expertise"
    }
  ],

  // 📊 Enhanced Response Metadata
  "response_metadata": {
    "response_type": "single_match",
    "confidence_level": "medium",
    "search_quality": {
      "average_score": 1.046788168,
      "score_distribution": {
        "excellent": 1,
        "good": 0,
        "fair": 0,
        "poor": 0
      },
      "top_score": 1.046788168,
      "consistency": 1.0
    },
    "timestamp": "2025-08-13T07:41:27.245484"
  }
}
```

**🎯 Session-Specific Features:**

- **Context Awareness**: Remembers previous searches and conversations
- **Session Persistence**: All UI components and data saved to session
- **Conversation Flow**: Building on previous interactions
- **Progressive Enhancement**: Each search builds on the conversation

**HTTP Status:** 200 (success) | 404 (session not found) | 422 (validation error)

---

### 16. 🧠 Enhanced Follow-up Questions (NEW)

**Endpoint:** `POST /api/v1/chat/sessions/{session_id}/followup`

**Purpose:** Ask intelligent follow-up questions with enhanced AI analysis

**Path Parameters:**

- `session_id`: The session ID

**Content-Type:** `application/json`

**Input:**

```json
{
  "question": "Why is John Doe the best match?",
  "context": {
    "last_search": "Python developers with backend experience",
    "candidates": ["John Doe"]
  }
}
```

**Required Fields:**

- `question`: The follow-up question

**Optional Fields:**

- `context`: Additional context for better analysis

**Enhanced Output:**

```json
{
  "session_id": "ce949674-f867-4a1e-b920-87e2a948a339",
  "question": "Why is John Doe the best match?",
  "answer": "🎯 ••Why These Candidates Were Selected•• ••John Doe•• • ••Broad skill set•• (21 skills) • ••Key technologies••: Javascript, Aws, Flask • ••Substantial experience•• (3 roles)",

  // 🎨 NEW: UI Components for Follow-up
  "ui_components": {
    "show_analysis": true,
    "candidate_comparison": true,
    "detailed_view": true
  },

  // 🔄 NEW: Conversation Flow Management
  "conversation_flow": {
    "next_suggestions": [
      "Ask another follow-up question",
      "Search for more candidates",
      "Refine the original search"
    ],
    "flow_type": "follow_up_analysis"
  },

  // ⚡ NEW: Smart Quick Actions
  "quick_actions": [
    {
      "label": "🔍 Find similar candidates",
      "action": "search",
      "query": "Find more candidates like these"
    },
    {
      "label": "📊 Detailed comparison",
      "action": "compare",
      "query": "Provide detailed comparison of these candidates"
    },
    {
      "label": "💼 Next steps",
      "action": "next",
      "query": "What should I do next with these candidates?"
    }
  ],

  // 📊 Response Metadata
  "response_metadata": {
    "response_type": "follow_up_analysis",
    "confidence_level": "high",
    "timestamp": "2025-08-13T07:41:39.830073"
  },
  "success": true
}
```

**🎯 Smart Follow-up Features:**

- **Context-Aware Answers**: Uses session history for better responses
- **Intelligent Analysis**: Deep understanding of candidate strengths
- **Interactive UI**: Components that adapt to the question type
- **Conversation Continuity**: Maintains natural dialogue flow

**Common Follow-up Questions:**

- "Why were these candidates selected?"
- "What are the key strengths of the top candidate?"
- "How do these candidates compare in terms of experience?"
- "Which candidate would be best for a startup environment?"
- "What technical skills do they have in common?"
- "Who has the most relevant cloud experience?"
- "Compare their educational backgrounds"
- "Which candidate has leadership experience?"

**HTTP Status:** 200 (success) | 404 (session not found)

---

### 17. Delete Chat Session

**Endpoint:** `DELETE /api/v1/chat/sessions/{session_id}`

**Purpose:** Delete (deactivate) a chat session

**Path Parameters:**

- `session_id`: The session ID to delete

**Example Request:**

```
DELETE /api/v1/chat/sessions/ce949674-f867-4a1e-b920-87e2a948a339
```

**Output:**

```json
{
  "session_id": "ce949674-f867-4a1e-b920-87e2a948a339",
  "message": "Session deleted successfully",
  "success": true
}
```

**HTTP Status:** 200 (success) | 404 (session not found)

---

## 🏠 ROOT ENDPOINT

### 18. API Root

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

## 🔧 DETAILED FRONTEND INTEGRATION GUIDE

### 🎨 UI Components Structure

The enhanced API provides structured data perfect for modern UI frameworks:

#### Candidate Cards Component

```javascript
// Example React component
const CandidateCard = ({ candidate }) => {
  return (
    <div className="candidate-card">
      <div className="candidate-header">
        <h3>{candidate.name}</h3>
        <span className="rank">#{candidate.rank}</span>
        <span className="score">{candidate.score.toFixed(2)}</span>
      </div>

      <div className="skills-section">
        {candidate.skills.slice(0, 8).map((skill) => (
          <span key={skill} className="skill-tag">
            {skill}
          </span>
        ))}
      </div>

      <div className="experience-summary">{candidate.experience_summary}</div>

      <div className="match-highlights">
        {candidate.match_highlights.map((highlight) => (
          <p key={highlight} className="highlight">
            {highlight}
          </p>
        ))}
      </div>
    </div>
  );
};
```

#### Search Quality Indicators

```javascript
const QualityIndicators = ({ quality }) => {
  return (
    <div className="quality-panel">
      <div className="metric">
        <span>Total Matches:</span>
        <strong>{quality.total_matches}</strong>
      </div>
      <div className="metric">
        <span>Average Score:</span>
        <strong>{quality.average_score.toFixed(2)}</strong>
      </div>
      <div className="metric">
        <span>Consistency:</span>
        <div className="progress-bar">
          <div
            style={{ width: `${quality.consistency * 100}%` }}
            className="progress-fill"
          />
        </div>
      </div>
    </div>
  );
};
```

#### Experience Distribution Chart

```javascript
const ExperienceChart = ({ data }) => {
  const total = Object.values(data).reduce((sum, val) => sum + val, 0);

  return (
    <div className="experience-chart">
      {Object.entries(data).map(([level, count]) => (
        <div key={level} className="chart-segment">
          <span className="level">{level}</span>
          <div className="bar">
            <div
              className="fill"
              style={{ width: `${(count / total) * 100}%` }}
            />
          </div>
          <span className="count">{count}</span>
        </div>
      ))}
    </div>
  );
};
```

#### Quick Actions Panel

```javascript
const QuickActions = ({ actions, onAction }) => {
  return (
    <div className="quick-actions">
      {actions.map((action, index) => (
        <button
          key={index}
          className={`action-btn action-${action.action}`}
          onClick={() => onAction(action)}
        >
          {action.label}
        </button>
      ))}
    </div>
  );
};
```

### 🔄 Conversation Flow Management

#### Follow-up Questions

```javascript
const FollowUpQuestions = ({ questions, onQuestionClick }) => {
  return (
    <div className="follow-up-panel">
      <h4>💡 Ask follow-up questions:</h4>
      <div className="question-grid">
        {questions.map((question, index) => (
          <button
            key={index}
            className="question-btn"
            onClick={() => onQuestionClick(question)}
          >
            {question}
          </button>
        ))}
      </div>
    </div>
  );
};
```

#### Search Refinement Options

```javascript
const RefinementOptions = ({ options, onRefine }) => {
  return (
    <div className="refinement-panel">
      <h4>🔍 Refine your search:</h4>
      <div className="option-list">
        {options.map((option, index) => (
          <button
            key={index}
            className="refine-btn"
            onClick={() => onRefine(option)}
          >
            {option}
          </button>
        ))}
      </div>
    </div>
  );
};
```

### 📊 Real-time Search Analytics

#### Search Insights Dashboard

```javascript
const SearchInsights = ({ insights }) => {
  return (
    <div className="insights-panel">
      <div className="detected-domains">
        <h5>🎯 Detected Domains:</h5>
        <div className="domain-tags">
          {insights.detected_domains.map((domain) => (
            <span key={domain} className="domain-tag">
              {domain}
            </span>
          ))}
        </div>
      </div>

      <div className="technical-depth">
        <h5>🔧 Technical Depth:</h5>
        <span className={`depth-indicator depth-${insights.technical_depth}`}>
          {insights.technical_depth}
        </span>
      </div>

      <div className="confidence-meter">
        <h5>🎯 Intent Confidence:</h5>
        <div className="confidence-bar">
          <div
            className="confidence-fill"
            style={{ width: `${insights.intent_confidence * 100}%` }}
          />
        </div>
        <span>{(insights.intent_confidence * 100).toFixed(0)}%</span>
      </div>
    </div>
  );
};
```

### 🚀 Complete Integration Examples

#### Upload Files with Progress

```javascript
const uploadResumes = async (files, onProgress) => {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));

  const response = await fetch("/api/v1/resumes/upload", {
    method: "POST",
    body: formData,
    onUploadProgress: (progressEvent) => {
      const progress = (progressEvent.loaded / progressEvent.total) * 100;
      onProgress(progress);
    },
  });

  return await response.json();
};
```

#### Enhanced Session Management

```javascript
class ChatSessionManager {
  constructor() {
    this.currentSession = null;
    this.searchHistory = [];
  }

  async createSession(name) {
    const response = await fetch("/api/v1/chat/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: "user123", name }),
    });

    const result = await response.json();
    this.currentSession = result.session;
    return result;
  }

  async intelligentSearch(message, topK = 10) {
    if (!this.currentSession) {
      throw new Error("No active session");
    }

    const response = await fetch(
      `/api/v1/chat/sessions/${this.currentSession.id}/search`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, top_k: topK }),
      }
    );

    const result = await response.json();
    this.searchHistory.push({
      query: message,
      results: result.matches,
      timestamp: new Date(),
      ui_components: result.ui_components,
    });

    return result;
  }

  async askFollowUp(question) {
    const response = await fetch(
      `/api/v1/chat/sessions/${this.currentSession.id}/followup`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          context: {
            last_search:
              this.searchHistory[this.searchHistory.length - 1]?.query,
          },
        }),
      }
    );

    return await response.json();
  }

  async optimizeQuery(query) {
    const response = await fetch(
      `/api/v1/chat/optimize-query?query=${encodeURIComponent(query)}`,
      { method: "POST", headers: { "Content-Type": "application/json" } }
    );

    return await response.json();
  }

  async analyzeQuery(query) {
    const response = await fetch(
      `/api/v1/chat/analyze?message=${encodeURIComponent(query)}`,
      { method: "POST", headers: { "Content-Type": "application/json" } }
    );

    return await response.json();
  }
}
```

#### Complete Chat Interface Implementation

```javascript
const ChatInterface = () => {
  const [sessionManager] = useState(new ChatSessionManager());
  const [currentResults, setCurrentResults] = useState(null);
  const [queryAnalysis, setQueryAnalysis] = useState(null);
  const [isOptimizing, setIsOptimizing] = useState(false);

  const handleSearch = async (message) => {
    try {
      // Analyze query first
      const analysis = await sessionManager.analyzeQuery(message);
      setQueryAnalysis(analysis);

      // Perform intelligent search
      const results = await sessionManager.intelligentSearch(message);
      setCurrentResults(results);

      return results;
    } catch (error) {
      console.error("Search failed:", error);
    }
  };

  const handleOptimizeQuery = async (query) => {
    setIsOptimizing(true);
    try {
      const optimization = await sessionManager.optimizeQuery(query);
      return optimization;
    } finally {
      setIsOptimizing(false);
    }
  };

  const handleFollowUp = async (question) => {
    const followUpResult = await sessionManager.askFollowUp(question);
    return followUpResult;
  };

  const handleQuickAction = async (action) => {
    switch (action.action) {
      case "search":
        return await handleSearch(action.query);
      case "contact":
        // Implement contact functionality
        window.open(`mailto:candidate@example.com`);
        break;
      case "compare":
        return await handleFollowUp(action.query);
      case "refine":
        // Show refinement options
        break;
      default:
        console.log("Unknown action:", action);
    }
  };

  return (
    <div className="chat-interface">
      {/* Search Input with Real-time Analysis */}
      <SearchInput
        onSearch={handleSearch}
        onOptimize={handleOptimizeQuery}
        isOptimizing={isOptimizing}
        analysis={queryAnalysis}
      />

      {/* Results Display */}
      {currentResults && (
        <div className="results-section">
          {/* Candidate Cards */}
          <div className="candidates-grid">
            {currentResults.ui_components.candidate_cards.map((candidate) => (
              <CandidateCard key={candidate.id} candidate={candidate} />
            ))}
          </div>

          {/* Skill Tags */}
          <SkillTagCloud tags={currentResults.ui_components.skill_tags} />

          {/* Experience Chart */}
          <ExperienceChart
            data={currentResults.ui_components.experience_chart}
          />

          {/* Quality Indicators */}
          <QualityIndicators
            quality={currentResults.ui_components.quality_indicators}
          />

          {/* Search Insights */}
          <SearchInsights
            insights={currentResults.ui_components.search_insights}
          />

          {/* Follow-up Questions */}
          <FollowUpQuestions
            questions={currentResults.conversation_flow.follow_up_questions}
            onQuestionClick={handleFollowUp}
          />

          {/* Quick Actions */}
          <QuickActions
            actions={currentResults.quick_actions}
            onAction={handleQuickAction}
          />
        </div>
      )}
    </div>
  );
};
```

### 📱 RECOMMENDED UI ARCHITECTURE

#### 1. Dashboard Layout

```
┌─────────────────────────────────────────────────────────┐
│ Header (Health Status, User Menu)                       │
├─────────────────────────────────────────────────────────┤
│ Sidebar         │ Main Content Area                     │
│ - Sessions      │ ┌─────────────────────────────────┐   │
│ - Upload        │ │ Search Input (with real-time    │   │
│ - Analytics     │ │ analysis & optimization)        │   │
│                 │ └─────────────────────────────────┘   │
│                 │ ┌─────────────────────────────────┐   │
│                 │ │ Results Display:                │   │
│                 │ │ - Candidate Cards Grid          │   │
│                 │ │ - Skill Tags Cloud              │   │
│                 │ │ - Experience Chart              │   │
│                 │ │ - Quality Indicators            │   │
│                 │ │ - Search Insights               │   │
│                 │ │ - Follow-up Questions           │   │
│                 │ │ - Quick Actions                 │   │
│                 │ └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

#### 2. Key UI Components Hierarchy

- **ChatInterface** (Main container)
  - **SearchInput** (with real-time analysis)
  - **ResultsDisplay**
    - **CandidateCardsGrid**
    - **SkillTagCloud**
    - **ExperienceChart**
    - **QualityIndicators**
    - **SearchInsights**
    - **FollowUpQuestions**
    - **QuickActions**
  - **SessionSidebar**
  - **UploadPanel**

#### 3. State Management Structure

```javascript
{
  // Session Management
  currentSession: SessionObject,
  sessionHistory: Array<SessionObject>,

  // Search State
  currentQuery: String,
  queryAnalysis: AnalysisObject,
  searchResults: ResultsObject,
  searchHistory: Array<SearchObject>,

  // UI State
  isSearching: Boolean,
  isOptimizing: Boolean,
  showAnalysis: Boolean,
  activeTab: String,

  // Real-time Features
  candidateCards: Array<CandidateObject>,
  skillTags: Array<String>,
  experienceChart: ChartData,
  qualityIndicators: QualityObject,
  searchInsights: InsightsObject,
  followUpQuestions: Array<String>,
  quickActions: Array<ActionObject>
}
```

### 🎯 IMPLEMENTATION PRIORITIES

#### Phase 1: Core Functionality

1. **Basic Search Interface** - Implement `/api/v1/chat/search`
2. **Session Management** - Create/list/delete sessions
3. **File Upload** - Resume upload with progress
4. **Results Display** - Basic candidate cards

#### Phase 2: Enhanced Features

1. **UI Components Integration** - Implement all UI components
2. **Real-time Analysis** - Query analysis and optimization
3. **Follow-up Intelligence** - Interactive follow-up questions
4. **Quick Actions** - Interactive action buttons

#### Phase 3: Advanced Features

1. **Search Insights Dashboard** - Real-time analytics
2. **Conversation Flow** - Advanced dialogue management
3. **Performance Optimization** - Caching and lazy loading
4. **Advanced Filters** - Complex search criteria

This comprehensive API documentation provides everything needed for seamless frontend integration with advanced AI-powered features!
