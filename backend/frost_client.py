import requests
import pandas as pd

from backend.config import (
    FROST_CLIENT_ID, FROST_CLIENT_SECRET, FROST_API_ENDPOINT,
    DEFAULT_STATION_ID, default_date_range, logger,
)


EMPTY_COLUMNS = ["station_id", "date", "precipitation_mm", "air_temperature_c"]

ELEMENT_PRECIP = "sum(precipitation_amount P1D)"
ELEMENT_TEMP = "mean(air_temperature P1D)"


def get_rainfall_data(station_id=None, days=365):
    """Fetch daily precipitation + mean air temperature from Frost.

    Returns a DataFrame with columns: station_id, date, precipitation_mm,
    air_temperature_c. Temperature may be NaN for dates where Frost has no
    observation. Returns an empty frame on error or when credentials are missing.
    """
    station_id = station_id or DEFAULT_STATION_ID
    start_date, end_date = default_date_range(days)
    time_period = f"{start_date}/{end_date}"

    if not FROST_API_ENDPOINT or not FROST_CLIENT_ID:
        logger.error("Frost API-konfigurasjon mangler. Sjekk .env-filen (CLIENT_ID, FROST_API_ENDPOINT).")
        return pd.DataFrame(columns=EMPTY_COLUMNS)

    params = {
        "sources": station_id,
        "elements": f"{ELEMENT_PRECIP},{ELEMENT_TEMP}",
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
        return pd.DataFrame(columns=EMPTY_COLUMNS)

    json_data = r.json()
    data = json_data.get("data", [])

    # Frost groups observations under a single entry per referenceTime, but each
    # observation has its own elementId. Walk the list and merge by date.
    by_date = {}
    for entry in data:
        date = entry["referenceTime"][:10]
        slot = by_date.setdefault(date, {
            "station_id": station_id,
            "date": date,
            "precipitation_mm": None,
            "air_temperature_c": None,
        })
        for obs in entry.get("observations", []):
            element_id = obs.get("elementId", "")
            value = obs.get("value")
            if element_id.startswith("sum(precipitation_amount"):
                slot["precipitation_mm"] = value
            elif element_id.startswith("mean(air_temperature"):
                slot["air_temperature_c"] = value

    rows = list(by_date.values())
    if not rows:
        return pd.DataFrame(columns=EMPTY_COLUMNS)
    df = pd.DataFrame(rows, columns=EMPTY_COLUMNS)
    # Database schema requires NOT NULL precipitation, so drop temperature-only days.
    df = df[df["precipitation_mm"].notna()].reset_index(drop=True)
    logger.info(
        "Hentet %d dager fra %s (temperaturobs: %d)",
        len(df), station_id, int(df["air_temperature_c"].notna().sum()),
    )
    return df


if __name__ == "__main__":
    df = get_rainfall_data()
    if not df.empty:
        print(df.head(10))
        print(f"\nTotal nedbør: {df['precipitation_mm'].sum():.1f} mm")
