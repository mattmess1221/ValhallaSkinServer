from fastapi import APIRouter

from . import auth, history, legacy, textures, user

router = APIRouter()
router.include_router(auth.router)
router.include_router(user.router)
router.include_router(textures.router)
router.include_router(history.router)
router.include_router(legacy.router)
