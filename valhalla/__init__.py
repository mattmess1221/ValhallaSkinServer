from importlib import metadata, resources
from pathlib import Path

__all__ = [
    "__usage__",
    "__version__",
]


def _read_text(path: str) -> str:
    p = Path(path)
    if p.exists():
        return p.read_text()
    return resources.read_text(__name__, path)


__metadata__ = metadata.metadata(__name__)
__version__ = __metadata__["Version"]
__usage__ = _read_text("USAGE.md")
