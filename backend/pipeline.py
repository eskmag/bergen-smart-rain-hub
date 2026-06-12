import argparse

from backend.config import DB_PATH, STATIONS, logger
from backend.database import init_db, store_observations
from backend.frost_client import get_rainfall_data


def run(db_path=None, days=365, stations=None):
    """Fetch rainfall data for each station and store it in the DB.

    Parameters
    ----------
    db_path:  path to the SQLite file; defaults to config.DB_PATH
    days:     how many calendar days of history to request from Frost
    stations: list of Frost station IDs to fetch; defaults to all STATIONS

    Returns
    -------
    int — total number of rows stored across all stations
    """
    db_path = db_path or DB_PATH
    station_list = stations if stations is not None else list(STATIONS)
    conn = init_db(db_path)
    total_rows = 0
    try:
        for station_id in station_list:
            df = get_rainfall_data(station_id=station_id, days=days)
            if df.empty:
                logger.warning(
                    "Ingen data hentet fra Frost API for stasjon %s — hopper over.",
                    station_id,
                )
                continue
            store_observations(conn, df)
            total_rows += len(df)
            logger.info(
                "Lagret %d observasjoner for %s i %s",
                len(df),
                station_id,
                db_path,
            )
    finally:
        conn.close()
    return total_rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Hent nedbørsdata fra Frost API og lagre i SQLite."
    )
    parser.add_argument(
        "--days",
        type=int,
        default=3650,
        help="Antall dager med historikk (standard: 3650 ≈ 10 år)",
    )
    parser.add_argument(
        "--station",
        type=str,
        default=None,
        help="Begrens til én stasjon (f.eks. SN50540). Standard: alle stasjoner.",
    )
    args = parser.parse_args()

    stations = [args.station] if args.station else None
    rows = run(days=args.days, stations=stations)

    if rows:
        print(f"\nOppsummering:")
        print(f"  Totalt lagret: {rows} observasjoner")
        print(f"  Stasjoner: {args.station or ', '.join(STATIONS)}")
    else:
        print("Ingen observasjoner ble lagret.")
