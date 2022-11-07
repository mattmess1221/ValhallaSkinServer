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


def generate_server_id():
    s = secrets.token_urlsafe(20)
    s = s.replace("_", "")
    s = s.replace("-", "")
    return s


class Settings(BaseSettings):
    env: Env = Env.PRODUCTION
    debug: bool = False

    texture_type_denylist: list[str] = ["cape"]

    secret_key: str = "dev"
    database_url = "sqlite:///./valhalla.db"

    # TODO this should be saved in the database
    server_id: str = Field(default_factory=generate_server_id)

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
