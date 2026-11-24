import httpx

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceException
from app.core.logging import get_logger
from app.schemas.trip import PlaceSnapshot

logger = get_logger(__name__)

# Places API (New) - Text Search. The field mask is mandatory: it selects (and bills) only these fields.
PLACES_URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = (
    "places.id,places.displayName,places.formattedAddress,"
    "places.location,places.rating,places.userRatingCount"
)
MAX_RESULTS = 8


def _parse_place(raw: dict) -> PlaceSnapshot | None:
    """Google place -> our PlaceSnapshot. Returns None for results we cannot pin on a map."""
    location = raw.get("location") or {}
    name = (raw.get("displayName") or {}).get("text")
    if not raw.get("id") or not name or "latitude" not in location or "longitude" not in location:
        return None
    return PlaceSnapshot(
        place_id=raw["id"],
        name=name,
        address=raw.get("formattedAddress", ""),
        lat=location["latitude"],
        lng=location["longitude"],
        rating=raw.get("rating"),
        rating_count=raw.get("userRatingCount"),
    )


async def search_places(query: str) -> list[PlaceSnapshot]:
    api_key = get_settings().google_places_api_key
    if not api_key:
        raise ExternalServiceException("Place search is not configured. Set GOOGLE_PLACES_API_KEY on the server.")

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,
    }
    body = {"textQuery": query, "maxResultCount": MAX_RESULTS}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(PLACES_URL, json=body, headers=headers)
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        # Log Google's reason for us; never forward it (it can echo key details) to the client.
        logger.error(f"Places API returned {e.response.status_code}: {e.response.text[:300]}")
        if e.response.status_code in (400, 403):
            raise ExternalServiceException(
                "Place search was rejected. Check that Places API (New) is enabled for the server key."
            )
        raise ExternalServiceException("Place search is temporarily unavailable.")
    except httpx.RequestError as e:
        logger.error(f"Places API request failed: {e}")
        raise ExternalServiceException("Place search is temporarily unavailable.")

    places = (_parse_place(raw) for raw in response.json().get("places", []))
    return [p for p in places if p is not None]