import os
from typing import List, Optional
import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class HttpConfig(BaseModel):
    timeout_seconds: int = 30
    max_concurrent_requests: int = 10
    max_retries: int = 3
    base_url: str = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1"


class EditionsFilterConfig(BaseModel):
    languages: List[str] = Field(default_factory=list)
    specific_editions: Optional[List[str]] = None


class VectorSearchConfig(BaseModel):
    vector_db_path: str = "vector_store"
    table_name: str = "hadith_vectors"
    provider: str = "sentence-transformers"
    model_name: str = "BAAI/bge-m3"
    device: str = "auto"
    openai_api_key: str = ""
    openai_model: str = "text-embedding-3-small"


class AppConfig(BaseModel):
    database_url: str = "sqlite+aiosqlite:///hadist.db"
    http: HttpConfig = Field(default_factory=HttpConfig)
    editions_filter: EditionsFilterConfig = Field(default_factory=EditionsFilterConfig)
    batch_size: int = 500
    vector_search: VectorSearchConfig = Field(default_factory=VectorSearchConfig)


def load_config(config_path: str = "config.yaml") -> AppConfig:
    config_dict = {}
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f) or {}

    env_db_url = os.getenv("DATABASE_URL")
    if env_db_url:
        config_dict["database_url"] = env_db_url

    return AppConfig(**config_dict)
