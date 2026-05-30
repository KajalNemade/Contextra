from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    database_url: str = Field(
        default="postgresql+psycopg://dcrs:dcrspass@localhost:5432/dcrs_db",
        description="PostgreSQL connection URL",
    )
    qdrant_url: str = Field(default="http://localhost:6333")
    ollama_url: str = Field(default="http://localhost:11434")
    gemini_api_key: str = Field(default="")

    repos_path: str = Field(default="./repos")
    max_files: int = Field(default=500)
    max_loc: int = Field(default=100_000)

    # Embedding config - stored so we can swap later
    embedding_model: str = Field(default="nomic-embed-text")
    embedding_dimension: int = Field(default=768)
    embedding_version: str = Field(default="v1")

    # LLM config
    llm_model: str = Field(default="llama3")
    context_soft_limit: int = Field(default=3000)
    context_hard_limit: int = Field(default=6000)

    # Secret detection patterns (comma-separated keywords)
    secret_patterns: str = Field(
        default="api_key,secret,password,token,private_key,aws_access,aws_secret"
    )

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()