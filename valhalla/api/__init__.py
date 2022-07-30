from fastapi import APIRouter

from . import v0, v1

router = APIRouter()
router.include_router(v1.router, prefix="/v1")
router.include_router(v0.router)
