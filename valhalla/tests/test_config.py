import pytest

from ..config import resolve_db


@pytest.mark.parametrize(
    ["url", "expected"],
    [
        [
            "sqlite:///file.db",
            "sqlite+aiosqlite:///file.db",
        ],
        [
            "postgres://user:pass@host:1234/dbname",
            "postgresql+asyncpg://user:pass@host:1234/dbname",
        ],
    ],
)
def test_database_url(url, expected):
    assert resolve_db(url) == expected
