from importlib import resources
from pathlib import Path

from .__version__ import __version__

__all__ = [
    "__version__",
    "__usage__",
]


def _read_text(path: str):
    p = Path(path)
    if p.exists():
        return p.read_text()
    return resources.read_text(__name__, path)


__usage__ = _read_text("USAGE.md")
# check if it's a git tag.
# a git tag will not be dev or formatted x.y.z
if "." not in __version__ != "dev":
    __version__ = f"git ({__version__[:6]})"
