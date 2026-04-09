"""
Configuration settings module.
Loads environment variables for database connections and JWT authentication.
"""

import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DB_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")

MODEL_NAME = os.getenv("MODEL_NAME")
TEMPERATURE = os.getenv("TEMPERATURE", "0.7")
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "google_genai")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "ai-tutor")
PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1")
PINECONE_CLOUD = os.getenv("PINECONE_CLOUD", "aws")
PINECONE_METRIC = os.getenv("PINECONE_METRIC", "cosine")
PINECONE_HOST = os.getenv("PINECONE_HOST")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DEFAULT_NAMESPACE = os.getenv("DEFAULT_NAMESPACE", "ai-assessment")


def require_setting(value, name):
    """
    Check if a required setting is set.

    Args:
        value: Value to check
        name: Name of the setting for error message

    Returns:
        The value if it is not None

    Raises:
        ValueError: If value is None
    """
    if value is None:
        raise ValueError(f"Required setting '{name}' is not set.")
    return value
