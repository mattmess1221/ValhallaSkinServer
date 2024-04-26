from importlib import metadata, resources
from pathlib import Path

__all__ = [
    "__version__",
    "__usage__",
]


def _read_text(path: str) -> str:
    p = Path(path)
    if p.exists():
        return p.read_text()
    return resources.read_text(__name__, path)


__version__ = metadata.version(__name__)
__usage__ = _read_text("USAGE.md")
