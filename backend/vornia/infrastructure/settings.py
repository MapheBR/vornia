"""Application settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Owner do schema: usado apenas por migrations/administracao.
    database_url: str = "postgresql://vornia:vornia@localhost:5432/vornia"
    # Runtime do FastAPI: role sujeita a RLS (nunca owner, nunca BYPASSRLS).
    database_url_app: str = ""
    # Bootstrap de tenant (register/login): role com BYPASSRLS.
    database_url_bootstrap: str = ""

    jwt_secret: str = ""
    access_token_expire_hours: int = 24
    cookie_secure: bool = True
    cors_origins: str = ""  # lista separada por vírgulas (dev: localhost:3000)


settings = Settings()
