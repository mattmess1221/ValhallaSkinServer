import pytest

from valhalla.config import Settings


@pytest.mark.parametrize(
    ["url", "expected"],
    [
        [
            "sqlite:///file.db",
            "sqlite+aiosqlite:///file.db",
        ],
        [
            "postgres://user:pass@host:1234/dbname",
            "postgresql+psycopg://user:pass@host:1234/dbname",
        ],
    ],
)
def test_database_url(url: str, expected: str) -> None:
    config = Settings.model_validate({"database_url": url})
    assert str(config.database_url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "https://textures.minelittlepony-mod.com/textures",
        "https://textures.minelittlepony-mod.com/textures/",
    ],
)
def test_texture_url(url: str) -> None:
    config = Settings.model_validate({"textures_url": url})

    assert str(config.textures_url).endswith("/")
