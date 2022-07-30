import secrets
from enum import Enum

from pydantic import AnyHttpUrl, BaseSettings, Field


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

    dashboard_dev_server: AnyHttpUrl = Field("http://localhost:5173")

    secret_key: str = "dev"
    database_url = "sqlite:///./valhalla.db"

    # TODO this should be saved in the database
    server_id: str = Field(default_factory=secrets.token_urlsafe)

    textures_fs: str = "file://./textures/"

    raygun_apikey: str | None = None
    xbox_live_client_id: str | None = None
    xbox_live_client_secret: str | None = None

    xbox_live_server_metadata_url: str = (
        "https://login.live.com/.well-known/openid-configuration"
    )
    xbox_live_client_kwargs: dict = {"scope": "XboxLive.signin offline_access"}

    class Config:
        env_file = ".env"


settings = Settings()  # type: ignore
