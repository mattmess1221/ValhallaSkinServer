import pathlib
import urllib.parse
from dataclasses import dataclass
from io import BytesIO
from typing import TYPE_CHECKING, Annotated, Any, Protocol

import boto3
import botocore.exceptions
from fastapi import Depends
from typing_extensions import Self

from .config import settings

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client


class Filesystem(Protocol):
    def exists(self) -> bool: ...
    def write_bytes(self, data: bytes) -> Any: ...  # noqa: ANN401
    def __truediv__(self, key: str) -> Self: ...


@dataclass
class S3Path:
    s3_client: "S3Client"
    bucket: str
    path: str

    def exists(self) -> bool:
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=self.path)
        except botocore.exceptions.ClientError as e:
            if e.response.get("Error", {}).get("Code") == "404":
                return False
            raise
        else:
            return True

    def write_bytes(self, data: bytes) -> None:
        self.s3_client.upload_fileobj(BytesIO(data), self.bucket, self.path)

    def __truediv__(self, key: str) -> Self:
        return type(self)(self.s3_client, self.bucket, f"{self.path}/{key}")


def textures_fs() -> str:
    return settings.textures_fs


def get_filesystem(textures_fs: Annotated[str, Depends(textures_fs)]) -> Filesystem:
    url = urllib.parse.urlparse(textures_fs)

    if url.scheme == "file":
        path = pathlib.Path(url.path.removeprefix("/"))
        if not path.exists():
            path.mkdir(parents=True)
        return path

    if url.scheme == "s3":
        s3_client = boto3.client("s3")
        bucket = url.netloc
        path = url.path
        return S3Path(s3_client, bucket, path)

    raise NotImplementedError(f"{url.scheme} is not implemented")


@dataclass
class Files:
    fs: Annotated[Filesystem, Depends(get_filesystem)]

    def put_file(self, skin_hash: str, data: bytes) -> None:
        """Save a texture to the file system"""

        file = self.fs / skin_hash

        if not file.exists():
            file.write_bytes(data)
