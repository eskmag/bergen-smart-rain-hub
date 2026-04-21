import requests
import pandas as pd

from backend.config import (
    FROST_CLIENT_ID, FROST_CLIENT_SECRET, FROST_API_ENDPOINT,
    DEFAULT_STATION_ID, default_date_range, logger,
)


def get_rainfall_data(station_id=None, days=365):
    station_id = station_id or DEFAULT_STATION_ID
    start_date, end_date = default_date_range(days)
    time_period = f"{start_date}/{end_date}"

    if not FROST_API_ENDPOINT or not FROST_CLIENT_ID:
        logger.error("Frost API-konfigurasjon mangler. Sjekk .env-filen (CLIENT_ID, FROST_API_ENDPOINT).")
        return pd.DataFrame(columns=["station_id", "date", "precipitation_mm"])

    params = {
        "sources": station_id,
        "elements": "sum(precipitation_amount P1D)",
        "referencetime": time_period,
    }

    try:
        r = requests.get(
            FROST_API_ENDPOINT, params=params,
            auth=(FROST_CLIENT_ID, FROST_CLIENT_SECRET),
            timeout=30,
        )
        r.raise_for_status()
    except requests.RequestException as e:
        logger.warning("Feil ved henting av data fra Frost API: %s", e)
        return pd.DataFrame(columns=["station_id", "date", "precipitation_mm"])

    json_data = r.json()
    data = json_data.get("data", [])

    rows = []
    for entry in data:
        date = entry["referenceTime"][:10]
        value = entry["observations"][0]["value"]
        rows.append({
            "station_id": station_id,
            "date": date,
            "precipitation_mm": value,
        })

    df = pd.DataFrame(rows)
    logger.info("Hentet %d dager med nedbørsdata for %s", len(df), station_id)
    return df


if __name__ == "__main__":
    df = get_rainfall_data()
    if not df.empty:
        print(df.head(10))
        print(f"\nTotal nedbør: {df['precipitation_mm'].sum():.1f} mm")
