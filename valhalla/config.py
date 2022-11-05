import secrets
from enum import Enum

from pydantic import AnyHttpUrl, BaseSettings, Field

async_sql_drivers = {
    "sqlite": "aiosqlite",
    "postgres": "asyncpg",
}


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

    # TODO this should be saved in the database
    server_id: str = Field(default_factory=secrets.token_urlsafe)

    textures_fs: str = "file://./textures/"
    textures_url: AnyHttpUrl | None = None

    xbox_live_client_id: str | None = None
    xbox_live_client_secret: str | None = None

    xbox_live_server_metadata_url: str = (
        "https://login.live.com/.well-known/openid-configuration"
    )
    xbox_live_client_kwargs: dict = {"scope": "XboxLive.signin offline_access"}

    def get_database_url(self) -> str:
        db_url = self.database_url
        for db, driver in async_sql_drivers.items():
            if db_url.startswith(f"{db}://"):
                db_url = db_url.replace(f"{db}://", f"{db}+{driver}://")
                break
        return db_url

    class Config:
        env_file = ".env"


settings = Settings()  # type: ignore
