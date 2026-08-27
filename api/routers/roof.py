from fastapi import APIRouter, HTTPException, Query

from backend.buildings import FootprintUnavailable, footprint_for
from api.schemas import RoofFootprintResponse

router = APIRouter()


@router.get("/roof/footprint", response_model=RoofFootprintResponse)
def get_roof_footprint(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    """Building outline at a coordinate, proxied from OSM.

    Proxied rather than called from the browser: Overpass returns a
    deterministic 406 for requests carrying a deployed site's Referer, and OSM's
    policy wants an identifying User-Agent that a browser cannot set.
    """
    try:
        geometry = footprint_for(lat, lon)
    except FootprintUnavailable:
        # 503 rather than 500: nothing is wrong with the request, the upstream
        # is simply unavailable and the caller may reasonably try later.
        raise HTTPException(
            status_code=503,
            detail="Bygningsdata er utilgjengelig akkurat nå. Prøv igjen om litt.",
        )
    return RoofFootprintResponse(found=geometry is not None, geometry=geometry)
