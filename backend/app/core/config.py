from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # MongoDB
    mongodb_uri: str
    mongodb_db_name: str = "travel_planner"

    # Optional integrations: the app boots without them and the
    # feature that needs a key raises a clear error when used.
    google_places_api_key: str = ""
    google_api_key: str = ""

    # App
    app_env: str = "development"
    frontend_url: str = "http://localhost:5173"

    # Uploads
    max_upload_mb: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()