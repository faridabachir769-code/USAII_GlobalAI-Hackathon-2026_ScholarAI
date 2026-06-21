"""
CORE CONFIGURATION MODULE
========================

This module handles all application settings and configuration.
It uses Pydantic Settings for type-safe environment variable management.

KEY CONCEPTS:
- Environment variables are loaded from .env file
- Settings are validated using Pydantic (prevents invalid configs)
- Using BaseSettings ensures type safety and IDE autocomplete
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application Settings

    All configuration values are loaded from environment variables.
    Example: DATABASE_URL env var → database_url attribute

    Why use this pattern?
    - Type safety: You get IDE hints and validation
    - Centralized: All config in one place
    - Flexible: Easy to override for testing
    """

    # Database Configuration
    # Default to SQLite for development, override with .env for production
    database_url: str = "sqlite:///./test.db"
    database_echo: bool = True  # Print SQL queries (helpful for learning)

    # Server Configuration
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    debug: bool = True

    # App Configuration
    app_name: str = "ScholarAI Backend"
    app_version: str = "0.1.0"

    # OpenAI / LLM Configuration
    openai_api_key: str = ""  # Set via .env
    openai_model: str = "gpt-4"  # Model for analysis
    openai_embedding_model: str = "text-embedding-3-small"  # Model for embeddings
    openai_embedding_dimensions: int = 1536  # Dimensions of embedding vectors

    # Supabase Configuration (for production with PostgreSQL)
    supabase_url: str = ""  # Set via .env
    supabase_key: str = ""  # Set via .env
    supabase_enabled: bool = False  # True when using Supabase PostgreSQL

    # RAG Configuration
    vector_search_top_k: int = 10  # Number of schemes to retrieve in vector search
    embedding_batch_size: int = 10  # Process embeddings in batches

    # Decision Engine Configuration
    decision_engine_weights: dict = {
        "eligibility": 0.40,  # 40% weight
        "benefit": 0.25,  # 25% weight
        "goal_alignment": 0.25,  # 25% weight
        "complexity": 0.10,  # 10% weight (lower is better)
    }

    class Config:
        """
        Pydantic Config
        - env_file: Load variables from .env file
        - case_sensitive: False = environment vars are case-insensitive
        """

        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra env vars


# Create a global settings instance
# Usage: from config import settings → settings.database_url
settings = Settings()
