from fastapi import APIRouter

from . import auth, user

router = APIRouter(tags=["v2"])
router.include_router(auth.router, prefix="/auth")
router.include_router(user.router, prefix="/user")
