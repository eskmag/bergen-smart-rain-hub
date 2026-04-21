from backend.config import DB_PATH, logger
from backend.database import init_db, store_observations
from backend.frost_client import get_rainfall_data


def run_pipeline(days=365, db_path=None):
    db_path = db_path or DB_PATH
    conn = init_db(db_path)
    try:
        df = get_rainfall_data(days=days)

        if df.empty:
            logger.warning("Ingen data hentet fra Frost API.")
            return df

        store_observations(conn, df)
        logger.info("Lagret %d observasjoner i %s", len(df), db_path)
        return df
    finally:
        conn.close()


if __name__ == "__main__":
    df = run_pipeline()
    if not df.empty:
        print(f"\nOppsummering:")
        print(f"  Periode: {df['date'].min()} til {df['date'].max()}")
        print(f"  Total nedbør: {df['precipitation_mm'].sum():.1f} mm")
        print(f"  Gjennomsnitt per dag: {df['precipitation_mm'].mean():.1f} mm")
