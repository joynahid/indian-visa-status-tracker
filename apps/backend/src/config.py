"""Application configuration loaded from environment."""

from functools import cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    comma_separated_proxy_urls: str = ""
    is_production: bool = False
    database_url: str = ""
    two_captcha_key: str = ""
    track_cache_ttl_seconds: int = 120
    status_check_secret: str = ""


@cache
def get_settings() -> Settings:
    return Settings()
