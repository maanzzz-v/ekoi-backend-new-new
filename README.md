# Resume Indexer API

A resume parser and indexer that extracts information from resumes and stores it in a vector database for efficient search and retrieval.

## Quick Start

### 1. Setup
```bash
git clone https://github.com/Aksaykanthan/resume-index
cd resume-index
uv venv
source .venv/bin/activate
uv sync
```

### 2. Configure Environment
```bash
cp .env.example .env
```

### 3. Start Server
```bash
uv run src/main.py
```

API available at: http://localhost:8000
Documentation: http://localhost:8000/docs

## API Endpoints

### Health Check
- `GET /api/v1/health/` - Basic health status
- `GET /api/v1/health/detailed` - Detailed system status

### Resume Management
- `POST /api/v1/resumes/upload` - Upload resume files (PDF, DOCX, TXT)
- `POST /api/v1/resumes/search` - Search resumes by vector similarity
- `GET /api/v1/resumes/` - List all resumes with pagination
- `GET /api/v1/resumes/{id}` - Get specific resume details
- `DELETE /api/v1/resumes/{id}` - Delete a resume

### Chat Search
- `POST /api/v1/chat/search` - Natural language resume search
- `POST /api/v1/chat/analyze` - Analyze search query intent


