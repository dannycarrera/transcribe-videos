import os
import sys
from pathlib import Path
from pydantic_settings import BaseSettings


ENVIRONMENTS = {
    "development": ".env.dev",
    "test": ".env.test",
    "production": ".env.prod",
}

# Load environment variables from .env file based on the APP_ENV env var
app_env = os.getenv("APP_ENV")
env_file = None

# Load env file if APP_ENV is set, otherwise defaults will be loaded
if app_env is not None:
    if app_env not in ENVIRONMENTS.keys():
        valid = ', '.join(ENVIRONMENTS.keys())
        print(f"Error: Invalid or missing APP_ENV='{app_env}'. Must be one of: {valid}")
        sys.exit(1)  # Exit with error
    else:
        env_file = ENVIRONMENTS[app_env]
        if not os.path.exists(env_file):
            print(f"Environment file {env_file} for APP_ENV={app_env} not found. Default settings will be applied.")

class Config(BaseSettings):
    """Application settings loaded from environment variables."""
    env: str = app_env or "Unknown"
    llama_models_dir: Path = "llm_models"
    hf_repo_id: str = "unsloth/Llama-3.2-1B-Instruct-GGUF"
    hf_model_filename: str = "Llama-3.2-1B-Instruct-Q2_K.gguf"
    llama_n_gpu_layers: int = -1  # Use all available GPU layers
    llama_context_size: int = 2048
    uploads_path: Path = "uploads"
    chroma_db_path: Path = "chroma_db"

    class Config:
        env_file = env_file

# Instantiate settings for easy access
config = Config()
