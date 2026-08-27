"""Building footprint lookup from OpenStreetMap, via the Overpass API.

This deliberately runs server-side rather than in the browser. Two reasons, both
measured rather than assumed:

1. `overpass-api.de` fronts Overpass with Apache, which returns a deterministic
   406 when `Referer` is a deployed site — 4 of 4 attempts from the Render
   domain, and never once from `http://localhost:5173/`. That is precisely why
   the roof map worked in development and failed in production.
2. OSM's API policy requires a User-Agent identifying the application, and warns
   that impersonating another app gets you blocked. A browser will not let a
   script set its User-Agent at all.

Calling from here satisfies both, removes CORS from the picture entirely, and
lets us cache — which matters, because Overpass asks regular applications to
stay under roughly 100 queries a day.

FKB-Bygning would be the better source (official roof surfaces rather than
crowd-sourced outlines), but Geonorge marks it `AccessIsRestricted: True`: free
only to Norge digitalt parties, purchasable otherwise, and distributed as
county-wise file downloads with no queryable API. OSM is the only open source of
building polygons in Norway.
"""

import time

import requests

from backend.config import logger

# kumi.systems is a full-planet mirror and a reasonable second try. Deliberately
# absent: overpass.osm.ch, which answers 200 with CORS but serves a
# Switzerland-only extract — it returns zero buildings for Bergen, which would
# read as "no roof at this address" rather than as an outage.
OVERPASS_ENDPOINTS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
)

USER_AGENT = "BergenSmartRainHub/1.0 (+https://github.com/eskmag/bergen-smart-rain-hub)"

SEARCH_RADIUS_M = 35
REQUEST_TIMEOUT_S = 4

# Retry only transient load; see _attempt for what counts as transient.
RETRY_DELAYS_S = (0.5,)

# Hard ceiling on the whole lookup, not just one request. Render's shared egress
# IP is effectively rate-limited out of Overpass (which allows 2 slots per IP),
# so in production every attempt tends to time out — measured 73-111s to fail
# before this existed. Someone waiting on a spinner needs a fast "draw it
# yourself" far more than they need a sixth attempt.
TOTAL_BUDGET_S = 8

# ~1 m at Bergen's latitude, so a re-click on the same building reuses the entry
# instead of spending quota. Entries are held in-process: Render's free tier
# wipes local disk on restart anyway, so persisting would buy nothing, and
# writing to the git-tracked rain.db would dirty the working tree.
CACHE_PRECISION = 5
CACHE_TTL_S = 24 * 60 * 60

_cache: dict[tuple[float, float], tuple[float, dict | None]] = {}


class FootprintUnavailable(RuntimeError):
    """Overpass could not be reached, or declined to answer."""


def clear_cache() -> None:
    _cache.clear()


def _post(url: str, query: str, timeout: float = REQUEST_TIMEOUT_S):
    return requests.post(
        url,
        data={"data": query},
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )


def _ring_to_coords(geometry) -> list[list[float]]:
    """Overpass gives lat/lon objects; GeoJSON wants [lon, lat] pairs."""
    return [[p["lon"], p["lat"]] for p in geometry]


def _close(ring: list[list[float]]) -> list[list[float]]:
    return ring if ring[0] == ring[-1] else [*ring, ring[0]]


def _point_in_ring(lon: float, lat: float, ring: list[list[float]]) -> bool:
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def _pick(elements, lat: float, lon: float) -> dict | None:
    """Prefer the building the point actually falls inside, else the nearest hit."""
    fallback = None
    for el in elements:
        geometry = el.get("geometry")
        if not geometry and el.get("members"):
            outer = next(
                (m for m in el["members"] if m.get("type") == "way" and m.get("geometry")),
                None,
            )
            geometry = outer.get("geometry") if outer else None
        if not geometry or len(geometry) < 3:
            continue
        ring = _close(_ring_to_coords(geometry))
        if _point_in_ring(lon, lat, ring):
            return {"type": "Polygon", "coordinates": [ring]}
        if fallback is None:
            fallback = {"type": "Polygon", "coordinates": [ring]}
    return fallback


def _attempt(url: str, query: str, timeout: float = REQUEST_TIMEOUT_S):
    """Return (payload, retryable). payload is None when the attempt failed."""
    try:
        response = _post(url, query, timeout)
    except requests.RequestException as exc:
        logger.warning("Overpass-kall feilet mot %s: %s", url, exc)
        return None, True

    if response.status_code == 200:
        return response.json(), False

    # 406 and 429 are the server explicitly declining — a block or a rate limit.
    # The OSM wiki asks for a 30s pause, which no interactive request can wait
    # out, so we stop asking this endpoint instead of hammering it. 5xx is
    # transient load and worth another go; any other 4xx means our query is bad.
    retryable = response.status_code >= 500
    logger.warning(
        "Overpass svarte %s fra %s (retryable=%s)", response.status_code, url, retryable
    )
    return None, retryable


def _query(lat: float, lon: float) -> str:
    return (
        f"[out:json][timeout:25];"
        f'(way(around:{SEARCH_RADIUS_M},{lat},{lon})["building"];'
        f'relation(around:{SEARCH_RADIUS_M},{lat},{lon})["building"];);'
        f"out geom;"
    )


def footprint_for(lat: float, lon: float) -> dict | None:
    """Return the GeoJSON Polygon geometry of the building at (lat, lon).

    Returns None when OSM simply has no building there — a real answer, and one
    worth caching. Raises FootprintUnavailable when no endpoint would answer.
    """
    key = (round(lat, CACHE_PRECISION), round(lon, CACHE_PRECISION))
    hit = _cache.get(key)
    if hit is not None and time.time() - hit[0] < CACHE_TTL_S:
        return hit[1]

    query = _query(lat, lon)
    started = time.monotonic()
    first = True
    for url in OVERPASS_ENDPOINTS:
        for attempt in range(len(RETRY_DELAYS_S) + 1):
            remaining = TOTAL_BUDGET_S - (time.monotonic() - started)
            # Always allow one attempt, then stop as soon as the budget is spent.
            if not first and remaining <= 0:
                raise FootprintUnavailable("Overpass svarte ikke innen tidsbudsjettet")
            first = False
            if attempt:
                time.sleep(RETRY_DELAYS_S[attempt - 1])
            payload, retryable = _attempt(
                url, query, min(REQUEST_TIMEOUT_S, max(remaining, 0.5))
            )
            if payload is not None:
                geometry = _pick(payload.get("elements", []), lat, lon)
                _cache[key] = (time.time(), geometry)
                return geometry
            if not retryable:
                break

    raise FootprintUnavailable("Overpass er utilgjengelig")
