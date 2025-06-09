import os
import sys
from pathlib import Path
from pydantic import HttpUrl
from pydantic_settings import BaseSettings


ENVIRONMENTS = {
    "development": ".env.dev",
    "test": ".env.test",
    "production": ".env.prod",
}

# Load environment variables from .env file based on the APP_ENV env var
app_env = os.getenv("APP_ENV")
env = "Unknown"

# Load env file if APP_ENV is set, otherwise defaults will be loaded
if app_env is not None:
    if app_env not in ENVIRONMENTS.keys():
        valid = ', '.join(ENVIRONMENTS.keys())
        print(f"Error: Invalid or missing APP_ENV '{app_env}'. Must be one of: {valid}")
        sys.exit(1)  # Exit with error
    else:
        env = ENVIRONMENTS[app_env]


class Config(BaseSettings):
    """Application settings loaded from environment variables."""
    env: str = env
    ollama_url: HttpUrl = "http://localhost:11434"
    ollama_model: str = "llama3.2:1b-instruct-q2_K"
    uploads_path: Path = "uploads"
    chroma_db_path: Path = "chroma_db"

    class Config:
        env_file = app_env

# Instantiate settings for easy access
config = Config()