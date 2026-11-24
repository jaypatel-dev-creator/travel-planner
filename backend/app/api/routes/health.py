from fastapi import APIRouter, Response

from app.core.logging import get_logger
from app.db.mongo import ping

router = APIRouter()
logger = get_logger(__name__)


@router.get("/health", tags=["Health"])
async def health(response: Response):
    """Liveness check. 200 if MongoDB answers a ping, 503 if not."""
    try:
        await ping()
    except Exception as e:
        logger.error(f"Health check DB ping failed: {e}")
        response.status_code = 503
        return {"status": "degraded", "database": "unreachable"}
    return {"status": "ok", "database": "ok"}