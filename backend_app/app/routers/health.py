
from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/ping")
async def ping():
    """
    Health check endpoint.
    Returns simple status to verify API is running.
    """
    return {"status": "ok", "message": "pong"}
