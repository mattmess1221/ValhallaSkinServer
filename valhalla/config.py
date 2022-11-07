import secrets
from enum import Enum
from urllib.parse import urlparse

from pydantic import AnyHttpUrl, BaseSettings, Field

async_sql_drivers = {
    "sqlite": "sqlite+aiosqlite",
    "postgres": "postgresql+asyncpg",
}


def resolve_db(url: str):
    url_parts = urlparse(url)
    if url_parts.scheme in async_sql_drivers:
        url_parts = url_parts._replace(scheme=async_sql_drivers[url_parts.scheme])
    url = url_parts.geturl()
    if not url_parts.netloc:
        url = url.replace(":/", ":///")
    return url


class Env(Enum):
    PRODUCTION = "prod"
    DEVELOPING = "dev"
    TESTING = "test"

    @property
    def isprod(self):
        return self is Env.PRODUCTION


class Settings(BaseSettings):
    env: Env = Env.PRODUCTION
    debug: bool = False

    secret_key: str = "dev"
    database_url = "sqlite:///./valhalla.db"

    textures_fs: str = "file://./textures/"
    textures_url: AnyHttpUrl | None = None

    xbox_live_client_id: str | None = None
    xbox_live_client_secret: str | None = None

    xbox_live_server_metadata_url: str = (
        "https://login.live.com/.well-known/openid-configuration"
    )
    xbox_live_client_kwargs: dict = {"scope": "XboxLive.signin offline_access"}

    def get_database_url(self) -> str:
        return resolve_db(self.database_url)

    def get_textures_url(self) -> str | None:
        url: str | None = self.textures_url
        if url and not url.endswith("/"):
            url += "/"
        return url

    class Config:
        env_file = ".env"


settings = Settings()  # type: ignore
