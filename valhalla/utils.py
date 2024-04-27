from collections.abc import AsyncGenerator, AsyncIterator
from typing import Annotated, Any

import httpx
from aiofiles.tempfile import TemporaryFile
from fastapi import Header, HTTPException, UploadFile, status
from starlette.datastructures import UploadFile as StarletteUploadFile

kb = 1024
mb = kb * 1024

MAX_UPLOAD_SIZE = 5 * mb


async def download_file(url: str, max_size: int = MAX_UPLOAD_SIZE) -> bytes:
    async with httpx.AsyncClient() as http:
        try:
            head_response = await http.head(url)
            head_response.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error fetching file: {e}",
            ) from None

        file_size = head_response.headers.get("content-length")
        if not file_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="file Content-Length is missing",
            )
        if file_size and int(file_size) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="file Content-Length is too big",
            )

        async with http.stream("GET", url) as resp:
            file_size = int(resp.headers["content-length"])
            return await read_upload(resp.aiter_bytes(), file_size)


async def read_upload(file: UploadFile | AsyncIterator[bytes], file_size: int) -> bytes:
    if isinstance(file, StarletteUploadFile):
        file = iter_upload_file(file)
    real_file_size = 0
    async with TemporaryFile() as temp:
        async for chunk in file:
            real_file_size += len(chunk)
            if real_file_size > file_size:
                raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
            await temp.write(chunk)
        await temp.seek(0)
        return await temp.read()


async def valid_content_length(
    content_length: Annotated[int, Header(le=MAX_UPLOAD_SIZE)],
) -> int:
    return content_length


async def iter_upload_file(file: UploadFile) -> AsyncGenerator[bytes, Any]:
    while chunk := await file.read(1024):
        yield chunk
