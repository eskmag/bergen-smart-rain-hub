from backend.database import init_db, store_observations
from backend.frost_client import get_rainfall_data


def run_pipeline(days=365, db_path="data/rain.db"):
    conn = init_db(db_path)
    df = get_rainfall_data(days=days)

    if df.empty:
        print("Ingen data hentet fra Frost API.")
        conn.close()
        return df

    store_observations(conn, df)
    print(f"Lagret {len(df)} observasjoner i {db_path}")
    conn.close()
    return df


if __name__ == "__main__":
    df = run_pipeline()
    if not df.empty:
        print(f"\nOppsummering:")
        print(f"  Periode: {df['date'].min()} til {df['date'].max()}")
        print(f"  Total nedbør: {df['precipitation_mm'].sum():.1f} mm")
        print(f"  Gjennomsnitt per dag: {df['precipitation_mm'].mean():.1f} mm")
