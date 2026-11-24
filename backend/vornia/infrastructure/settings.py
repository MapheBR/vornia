"""Application settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql://vornia:vornia@localhost:5432/vornia"
    jwt_secret: str = ""
    access_token_expire_hours: int = 24
    cookie_secure: bool = True


settings = Settings()
