from fastapi import APIRouter, HTTPException, Query

from backend.config import DB_PATH, DEFAULT_STATION_ID, STATIONS, default_date_range
from backend.database import init_db, get_observations
from api.schemas import Observation

router = APIRouter()


@router.get("/observations", response_model=list[Observation])
def get_obs(
    days: int = Query(default=365, ge=1, le=3650),
    station: str = Query(default=DEFAULT_STATION_ID),
):
    if station not in STATIONS:
        raise HTTPException(status_code=422, detail=f"Ukjent stasjon: {station!r}")
    start, end = default_date_range(days)
    conn = init_db(DB_PATH)
    df = get_observations(conn, start, end, station_id=station)
    conn.close()

    return [
        Observation(
            date=row["date"] if isinstance(row["date"], str) else row["date"].strftime("%Y-%m-%d"),
            precipitation_mm=row["precipitation_mm"],
            air_temperature_c=row.get("air_temperature_c"),
        )
        for _, row in df.iterrows()
    ]
