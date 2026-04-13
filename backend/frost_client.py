import requests
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta


def get_rainfall_data(station_id="SN50540", days=365):
    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    endpoint = os.getenv("FROST_API_ENDPOINT")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    time_period = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"

    params = {
        "sources": station_id,
        "elements": "sum(precipitation_amount P1D)",
        "referencetime": time_period,
    }

    try:
        r = requests.get(endpoint, params=params, auth=(client_id, client_secret))
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"Feil ved henting av data fra Frost API: {e}")
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
    print(f"Hentet {len(df)} dager med nedbørsdata for {station_id}")
    return df


if __name__ == "__main__":
    df = get_rainfall_data()
    if not df.empty:
        print(df.head(10))
        print(f"\nTotal nedbør: {df['precipitation_mm'].sum():.1f} mm")
