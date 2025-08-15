"""Application configuration settings."""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # dotenv is optional
    pass


class Settings(BaseSettings):
    """Application settings configuration."""

    # Application settings
    app_name: str = Field(default="Resume Index API", env="APP_NAME")
    app_version: str = Field(default="0.1.0", env="APP_VERSION")
    debug: bool = Field(default=True, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # LLM Provider settings
    llm_provider: str = Field(
        default="sentence-transformers", env="LLM_PROVIDER"
    )  # openai, gemini, ollama, vllm, sentence-transformers

    # OpenAI settings
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="text-embedding-ada-002", env="OPENAI_MODEL")
    openai_chat_model: str = Field(default="gpt-4-turbo-preview", env="OPENAI_CHAT_MODEL")

    # Gemini settings
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    gemini_model: str = Field(default="models/embedding-001", env="GEMINI_MODEL")

    # Ollama settings
    ollama_base_url: str = Field(
        default="http://localhost:11434", env="OLLAMA_BASE_URL"
    )
    ollama_model: str = Field(default="nomic-embed-text", env="OLLAMA_MODEL")

    # vLLM settings
    vllm_base_url: Optional[str] = Field(default=None, env="VLLM_BASE_URL")
    vllm_model: str = Field(default="BAAI/bge-large-en-v1.5", env="VLLM_MODEL")
    vllm_api_key: Optional[str] = Field(default=None, env="VLLM_API_KEY")

    # Pinecone settings
    pinecone_api_key: Optional[str] = Field(default=None, env="PINECONE_API_KEY")
    pinecone_environment: Optional[str] = Field(
        default=None, env="PINECONE_ENVIRONMENT"
    )
    pinecone_index_name: str = Field(default="resume-index", env="PINECONE_INDEX_NAME")

    # MongoDB settings
    mongodb_url: str = Field(default="mongodb://localhost:27017", env="MONGODB_URL")
    mongodb_database: str = Field(default="resume_db", env="MONGODB_DATABASE")

    # File upload settings
    max_file_size_mb: int = Field(default=10, env="MAX_FILE_SIZE_MB")
    allowed_file_types: str = Field(default="pdf,docx,txt", env="ALLOWED_FILE_TYPES")

    # Slack settings
    slack_token: Optional[str] = Field(default=None, env="SLACK_TOKEN")

    @property
    def allowed_file_types_list(self) -> List[str]:
        """Get allowed file types as a list."""
        if isinstance(self.allowed_file_types, str):
            return [
                item.strip()
                for item in self.allowed_file_types.split(",")
                if item.strip()
            ]
        return self.allowed_file_types

    # Vector database settings
    vector_dimension: int = Field(default=768, env="VECTOR_DIMENSION")
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDING_MODEL"
    )

    class Config:
        """Pydantic config."""

        env_file = ".env.local"
        case_sensitive = False


# Global settings instance
settings = Settings()
