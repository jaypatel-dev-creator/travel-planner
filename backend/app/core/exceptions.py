from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger(__name__)


class TravelPlannerException(Exception):
    """Base class: every domain error carries a message and an HTTP status."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class InvalidIdException(TravelPlannerException):
    def __init__(self, value: str):
        super().__init__(message=f"'{value}' is not a valid id.", status_code=400)


class TripNotFoundException(TravelPlannerException):
    def __init__(self, trip_id: str):
        super().__init__(message=f"Trip '{trip_id}' not found.", status_code=404)


class DestinationNotFoundException(TravelPlannerException):
    def __init__(self, destination_id: str):
        super().__init__(message=f"Destination '{destination_id}' not found.", status_code=404)


class ActivityNotFoundException(TravelPlannerException):
    def __init__(self, activity_id: str):
        super().__init__(message=f"Activity '{activity_id}' not found.", status_code=404)


class DocumentNotFoundException(TravelPlannerException):
    def __init__(self, document_id: str):
        super().__init__(message=f"Document '{document_id}' not found.", status_code=404)


class BusinessRuleException(TravelPlannerException):
    """A request that is well-formed but breaks a domain rule (e.g. date outside the trip)."""

    def __init__(self, message: str):
        super().__init__(message=message, status_code=422)


class FileValidationException(TravelPlannerException):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message=message, status_code=status_code)


class ExternalServiceException(TravelPlannerException):
    """Google Places / Gemini failed or is not configured."""

    def __init__(self, message: str):
        super().__init__(message=message, status_code=502)


# --- Exception handlers ---

async def travel_planner_exception_handler(
    request: Request, exc: TravelPlannerException
) -> JSONResponse:
    if exc.status_code >= 500:
        logger.error(
            f"{exc.__class__.__name__} on {request.method} {request.url.path}: {exc.message}",
            exc_info=True,
        )
    else:
        logger.warning(
            f"{exc.__class__.__name__} on {request.method} {request.url.path}: {exc.message}"
        )

    # 4xx and 502 messages are written to be shown to the user, so we forward them.
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.__class__.__name__, "message": exc.message},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {exc}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"error": "InternalServerError", "message": "An unexpected error occurred."},
    )