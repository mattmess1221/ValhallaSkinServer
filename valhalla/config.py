import secrets
from typing import Annotated
from urllib.parse import urlparse

from pydantic import AfterValidator, AnyUrl, BeforeValidator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

async_sql_drivers = {
    "sqlite": "sqlite+aiosqlite",
    "postgres": "postgresql+psycopg",
}


def resolve_db(url: str) -> str:
    url_parts = urlparse(url)
    if url_parts.scheme in async_sql_drivers:
        url_parts = url_parts._replace(scheme=async_sql_drivers[url_parts.scheme])
    url = url_parts.geturl()
    if not url_parts.netloc:
        url = url.replace(":/", ":///")
    return url


def generate_server_id() -> str:
    s = secrets.token_urlsafe(20)
    s = s.replace("_", "")
    return s.replace("-", "")


def append_leading_slash(url: str | None) -> str | None:
    if url and not url.endswith("/"):
        url += "/"
    return url


DatabaseDSN = Annotated[str, AfterValidator(resolve_db)]
LeadingSlashURL = Annotated[AnyUrl, BeforeValidator(append_leading_slash)]


class Settings(BaseSettings):
    texture_type_denylist: frozenset[str] = frozenset({"cape"})

    secret_key: str = "dev"
    database_url: DatabaseDSN = "sqlite:///./valhalla.db"

    # TODO this should be saved in the database
    server_id: str = Field(default_factory=generate_server_id)

    textures_bucket: str | None = None
    textures_path: str = "textures"
    textures_url: LeadingSlashURL | None = None

    xbox_live_client_id: str | None = None
    xbox_live_client_secret: str | None = None

    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
    )


def get_settings() -> Settings:
    return Settings()


settings = Settings()
