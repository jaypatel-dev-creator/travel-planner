import asyncio
import time

import httpx

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceException
from app.core.logging import get_logger
from app.schemas.trip import PlaceSnapshot

logger = get_logger(__name__)

MAX_RESULTS = 8

# ---------- Google Places API (New) - used when GOOGLE_PLACES_API_KEY is set ----------
# The field mask is mandatory: it selects (and bills) only these fields.
GOOGLE_URL = "https://places.googleapis.com/v1/places:searchText"
GOOGLE_FIELD_MASK = (
    "places.id,places.displayName,places.formattedAddress,"
    "places.location,places.rating,places.userRatingCount"
)

# ---------- OpenStreetMap Nominatim - keyless fallback ----------
# Usage policy: identifying User-Agent, max 1 request/second, no keystroke autocomplete.
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_USER_AGENT = "travel-planner-assessment/1.0 (student project)"
NOMINATIM_MIN_INTERVAL = 1.0  # seconds between requests

_nominatim_lock = asyncio.Lock()
_nominatim_last_call = 0.0


def _parse_google_place(raw: dict) -> PlaceSnapshot | None:
    """Google place -> PlaceSnapshot. Returns None for results we cannot pin on a map."""
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


def _parse_osm_place(raw: dict) -> PlaceSnapshot | None:
    """Nominatim result -> PlaceSnapshot. OSM has no ratings, so rating stays None."""
    try:
        lat = float(raw["lat"])
        lng = float(raw["lon"])
        osm_type = raw["osm_type"]
        osm_id = raw["osm_id"]
    except (KeyError, TypeError, ValueError):
        return None

    display_name = (raw.get("display_name") or "").strip()
    name = (raw.get("name") or "").strip() or display_name.split(",")[0].strip()
    if not name:
        return None

    try:
        # Prefixed so OSM ids can never collide with Google place ids.
        return PlaceSnapshot(
            place_id=f"osm:{osm_type}:{osm_id}",
            name=name[:200],
            address=display_name[:400],
            lat=lat,
            lng=lng,
            rating=None,
            rating_count=None,
        )
    except ValueError:
        # Out-of-range coordinates etc.: skip the result instead of failing the whole search.
        return None


async def _search_google(query: str, api_key: str) -> list[PlaceSnapshot]:
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": GOOGLE_FIELD_MASK,
    }
    body = {"textQuery": query, "maxResultCount": MAX_RESULTS}

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(GOOGLE_URL, json=body, headers=headers)
        response.raise_for_status()

    places = (_parse_google_place(raw) for raw in response.json().get("places", []))
    return [p for p in places if p is not None]


async def _search_osm(query: str) -> list[PlaceSnapshot]:
    global _nominatim_last_call

    params = {"q": query, "format": "jsonv2", "limit": MAX_RESULTS}
    headers = {"User-Agent": NOMINATIM_USER_AGENT, "Accept-Language": "en"}

    # Serialise calls and space them >= 1s apart to respect Nominatim's policy.
    async with _nominatim_lock:
        wait = NOMINATIM_MIN_INTERVAL - (time.monotonic() - _nominatim_last_call)
        if wait > 0:
            await asyncio.sleep(wait)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(NOMINATIM_URL, params=params, headers=headers)
                response.raise_for_status()
        finally:
            _nominatim_last_call = time.monotonic()

    places = (_parse_osm_place(raw) for raw in response.json())
    return [p for p in places if p is not None]


async def search_places(query: str) -> list[PlaceSnapshot]:
    api_key = get_settings().google_places_api_key

    # 1) Google, when a key is configured. If Google fails, log why and fall through to OSM
    #    so place search keeps working instead of breaking the whole demo.
    if api_key:
        try:
            return await _search_google(query, api_key)
        except httpx.HTTPStatusError as e:
            # Log Google's reason for us; never forward it (it can echo key details) to the client.
            logger.error(f"Places API returned {e.response.status_code}: {e.response.text[:300]}")
        except httpx.RequestError as e:
            logger.error(f"Places API request failed: {e}")
        logger.warning("Google place search failed; falling back to OpenStreetMap.")

    # 2) OpenStreetMap fallback (no key needed).
    try:
        return await _search_osm(query)
    except httpx.HTTPStatusError as e:
        logger.error(f"Nominatim returned {e.response.status_code}: {e.response.text[:300]}")
    except httpx.RequestError as e:
        logger.error(f"Nominatim request failed: {e}")
    except ValueError as e:
        logger.error(f"Nominatim returned invalid JSON: {e}")
    raise ExternalServiceException("Place search is temporarily unavailable.")