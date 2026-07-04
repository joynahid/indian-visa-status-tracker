"""Application configuration loaded from environment."""

from functools import cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    comma_separated_proxy_urls: str = ""
    is_production: bool = False
    two_captcha_key: str = ""
    track_cache_ttl_seconds: int = 120
    firestore_project: str = "easy-indian-visa"
    firestore_database: str = "indian-visa-status"
    status_check_secret: str = ""


@cache
def get_settings() -> Settings:
    return Settings()
