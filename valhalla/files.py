from typing import Iterator

import fs
from fastapi import Depends
from fs.base import FS

from .config import settings


def get_filesystem() -> Iterator[FS]:
    with fs.open_fs(settings.textures_fs, writeable=True) as filesystem:
        yield filesystem


class Files:
    def __init__(self, filesystem: FS = Depends(get_filesystem)) -> None:
        self.fs = filesystem

    def put_file(self, skin_hash: str, file: bytes) -> None:
        """Save a texture to the file system"""

        if not self.fs.exists(skin_hash):
            with self.fs.open(skin_hash, "wb") as f:
                f.write(file)
