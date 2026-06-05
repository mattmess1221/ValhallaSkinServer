from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Protocol, Self, override

import boto3
import botocore.exceptions
from fastapi import Depends

from .config import Settings, get_settings

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client


class Filesystem(Protocol):
    def exists(self) -> bool: ...
    def write_bytes(self, data: bytes, *, content_type: str | None = None) -> int: ...
    def __truediv__(self, key: str) -> Self: ...


@dataclass
class FilePath(Filesystem):
    path: Path

    @override
    def exists(self) -> bool:
        return self.path.exists()

    @override
    def write_bytes(self, data: bytes, *, content_type: str | None = None) -> int:
        return self.path.write_bytes(data)

    @override
    def __truediv__(self, key: str) -> Self:
        return type(self)(self.path / key)


@dataclass
class S3Path(Filesystem):
    s3_client: S3Client
    bucket: str
    path: str

    @override
    def exists(self) -> bool:
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=self.path)
        except botocore.exceptions.ClientError as e:
            if e.response.get("Error", {}).get("Code") == "404":
                return False
            raise
        else:
            return True

    @override
    def write_bytes(self, data: bytes, *, content_type: str | None = None) -> int:
        extra = {}
        if content_type is not None:
            extra["ContentType"] = content_type
        self.s3_client.upload_fileobj(BytesIO(data), self.bucket, self.path, extra)
        return len(data)

    @override
    def __truediv__(self, key: str) -> Self:
        return type(self)(self.s3_client, self.bucket, f"{self.path}/{key}")


def get_filesystem(config: Annotated[Settings, Depends(get_settings)]) -> Filesystem:
    bucket = config.textures_bucket
    if bucket is None:
        # bucket not set, use local files for storage
        path = Path(config.textures_path)
        if not path.exists():
            path.mkdir(parents=True)
        return FilePath(path)

    # use s3 for storage
    s3_client = boto3.client("s3")
    return S3Path(s3_client, bucket, config.textures_path)


@dataclass
class Files:
    fs: Annotated[Filesystem, Depends(get_filesystem)]

    def put_file(self, skin_hash: str, data: bytes) -> None:
        """Save a texture to the file system"""

        file = self.fs / skin_hash

        if not file.exists():
            file.write_bytes(data, content_type="image/png")


def verify_aws_credentials() -> None:
    sts_client = boto3.client("sts")
    sts_client.get_caller_identity()
