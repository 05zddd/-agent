from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # LLM (DashScope)
    dashscope_api_key: str = ""
    llm_model: str = "qwen-max"

    # Amap
    amap_api_key: str = ""
    amap_js_api_key: str = ""

    # Embedding
    embedding_model: str = "text-embedding-v4"

    # ChromaDB
    chroma_persist_dir: str = "./data/chroma_db"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    cache_ttl: int = 3600

    # SQLite
    database_url: str = "sqlite:///./data/trip_planner.db"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Document
    max_file_size_mb: int = 20

    # Amap API base
    amap_base_url: str = "https://restapi.amap.com/v3"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
