# Resume Indexer API

A powerful resume parser and indexer that extracts key information from resumes and stores it in a vector database for efficient retrieval and search based on user queries.

## Features

- **Multi-format Support**: Process PDF, DOCX, and TXT resume files
- **Flexible LLM Providers**: Support for OpenAI, Google Gemini, Ollama, vLLM, and Sentence Transformers
- **Vector Storage**: Dual support for Pinecone and FAISS vector databases
- **MongoDB Integration**: Store resume metadata and extracted information
- **Smart Search**: Vector similarity search with relevance scoring
- **RESTful API**: FastAPI-based API with automatic documentation
- **Async Processing**: Efficient async processing for better performance

## Tech Stack

- **Framework**: FastAPI
- **Database**: MongoDB (metadata), Pinecone/FAISS (vectors)
- **LLM Providers**: OpenAI, Google Gemini, Ollama, vLLM, Sentence Transformers
- **Processing**: PyPDF2, python-docx, pandas
- **Validation**: Pydantic

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd resume-index
```

### 2. Install Dependencies

Using UV (recommended):
```bash
uv sync
```

Using pip:
```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your preferred configuration:

```env
# Choose your LLM provider
LLM_PROVIDER=sentence-transformers  # or openai, gemini, ollama, vllm

# For OpenAI (if using openai provider)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=text-embedding-ada-002

# For Gemini (if using gemini provider)
GEMINI_API_KEY=your_gemini_api_key_here

# For Ollama (if using ollama provider - requires local installation)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=nomic-embed-text

# For vLLM (if using vllm provider - requires vLLM server)
VLLM_BASE_URL=http://localhost:8000
VLLM_MODEL=BAAI/bge-large-en-v1.5

# Vector Database (optional - will use FAISS if not configured)
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment

# MongoDB (optional - uses local MongoDB if not configured)
MONGODB_URL=mongodb://localhost:27017
```

### 4. Test LLM Provider

Test your LLM configuration:

```bash
python test_llm.py
```

### 5. Start the Server

```bash
uv run src/main.py
```

The API will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health

## API Endpoints

### Upload Resumes
```http
POST /api/v1/resumes/upload
Content-Type: multipart/form-data

files: [resume files]
```

### Search Resumes
```http
POST /api/v1/resumes/search
Content-Type: application/json

{
    "query": "Python developer with machine learning experience",
    "top_k": 10,
    "filters": {}
}
```

### List Resumes
```http
GET /api/v1/resumes/?skip=0&limit=50
```

### Get Resume Details
```http
GET /api/v1/resumes/{resume_id}
```

### Delete Resume
```http
DELETE /api/v1/resumes/{resume_id}
```

### Health Checks
```http
GET /api/v1/health/
GET /api/v1/health/detailed
GET /api/v1/health/llm-provider
```

## LLM Provider Configuration

### Sentence Transformers (Default - No API Key Required)
```env
LLM_PROVIDER=sentence-transformers
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```
Best for: Local development, privacy-focused deployments

### OpenAI
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=text-embedding-ada-002
```
Best for: Production, high-quality embeddings

### Google Gemini
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=models/embedding-001
```
Best for: Google ecosystem integration

### Ollama (Local)
```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=nomic-embed-text
```

First install Ollama:
```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Pull the embedding model
ollama pull nomic-embed-text
```
Best for: Local deployment, privacy, cost control

### vLLM (Self-hosted)
```env
LLM_PROVIDER=vllm
VLLM_BASE_URL=http://localhost:8000
VLLM_MODEL=BAAI/bge-large-en-v1.5
```

Start vLLM server:
```bash
python -m vllm.entrypoints.openai.api_server \
    --model BAAI/bge-large-en-v1.5 \
    --port 8000
```
Best for: Self-hosted production, custom models

## Database Setup

### MongoDB (Required)
Install and start MongoDB locally, or use a cloud service like MongoDB Atlas.

### Pinecone (Optional)
1. Sign up at [Pinecone](https://www.pinecone.io/)
2. Create an index with 768 dimensions (or match your embedding model)
3. Add your API key and environment to `.env`

### FAISS (Automatic Fallback)
FAISS is used automatically as a fallback if Pinecone is not configured.

## Example Usage

### Upload Resumes
```python
import requests

files = [
    ('files', open('resume1.pdf', 'rb')),
    ('files', open('resume2.docx', 'rb')),
]

response = requests.post(
    'http://localhost:8000/api/v1/resumes/upload',
    files=files
)
print(response.json())
```

### Search for Candidates
```python
import requests

search_request = {
    "query": "Senior Python developer with AWS experience and machine learning background",
    "top_k": 5
}

response = requests.post(
    'http://localhost:8000/api/v1/resumes/search',
    json=search_request
)

results = response.json()
for match in results['matches']:
    print(f"Score: {match['score']:.3f} - {match['file_name']}")
    print(f"Skills: {match['extracted_info']['skills']}")
```

## Project Structure

```
resume-index/
├── src/
│   ├── config/           # Configuration and settings
│   ├── controllers/      # API route handlers
│   ├── core/            # Core services (database, vector DB)
│   ├── exceptions/      # Custom exception classes
│   ├── models/          # Data models and schemas
│   ├── services/        # Business logic and services
│   └── main.py          # FastAPI application entry point
├── data/                # Data storage directory
├── .env.example         # Environment variables template
├── pyproject.toml       # Project dependencies
└── README.md           # This file
```

## Development

### Running Tests
```bash
python test_llm.py
```

### API Documentation
Access interactive API docs at http://localhost:8000/docs

### Logging
Logs are configured in `src/main.py`. Adjust log level in `.env`:
```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

## Production Deployment

1. **Environment**: Set `DEBUG=False` in production
2. **Database**: Use managed MongoDB service
3. **Vector DB**: Use Pinecone for production scale
4. **LLM Provider**: Consider OpenAI or self-hosted options based on volume
5. **Security**: Implement proper authentication and rate limiting
6. **Monitoring**: Add application monitoring and alerting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Your License Here]