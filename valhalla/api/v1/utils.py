from urllib.parse import urljoin

from fastapi import Request

from ...config import settings


def get_textures_url(request: Request) -> str:
    return settings.textures_url or urljoin(str(request.base_url), "textures/")
