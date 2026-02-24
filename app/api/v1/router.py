from fastapi import APIRouter
from app.api.v1.endpoints import registration, activation

router = APIRouter(prefix="/v1")
router.include_router(registration.router)
router.include_router(activation.router)
