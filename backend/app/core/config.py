from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Colorado Ice Atlas API"
    database_url: str | None = None
    data_dir: Path = ROOT / "frontend" / "public" / "data"
    processed_dir: Path = ROOT / "data" / "processed"
    cors_origins: str = "http://127.0.0.1:3847,http://localhost:3847,http://127.0.0.1:4173,http://localhost:4173"
    cache_seconds: int = 300


settings = Settings()
