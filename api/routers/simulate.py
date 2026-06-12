from fastapi import APIRouter, HTTPException

from backend.config import DB_PATH, DEFAULT_STATION_ID, STATIONS, default_date_range
from backend.database import init_db, get_observations
from backend.analysis import (
    Building, storage_simulation, emergency_summary, find_dry_spells,
    yearly_outcomes,
)
from backend.climate import apply_climate_projection, compare_scenarios
from api.schemas import (
    BeredskapsRequest, BeredskapsResponse, SimulationRow, DrySpell,
    ScenarioComparison, YearlyOutcome,
)

router = APIRouter()


def _load_df(days: int = 365, station: str = DEFAULT_STATION_ID):
    if station not in STATIONS:
        raise HTTPException(status_code=422, detail=f"Ukjent stasjon: {station!r}")
    start, end = default_date_range(days)
    conn = init_db(DB_PATH)
    df = get_observations(conn, start, end, station_id=station)
    conn.close()
    if df.empty:
        raise HTTPException(status_code=503, detail="Ingen nedbørsdata funnet. Kjør backend.pipeline.")
    return df


@router.post("/simulate/beredskap", response_model=BeredskapsResponse)
def simulate_beredskap(req: BeredskapsRequest):
    df = _load_df(station=req.station)
    df_scenario = apply_climate_projection(df, req.climate_scenario)

    # Long frame for per-year analysis (up to ~10 years)
    df_full = _load_df(days=3650, station=req.station)
    df_full_scenario = apply_climate_projection(df_full, req.climate_scenario)

    buildings = [
        Building(b.name, roof_area_m2=b.roof_area_m2, height_m=b.height_m)
        for b in req.buildings
    ]

    summary_raw = emergency_summary(df_scenario, buildings, req.tank_liters, req.population, req.efficiency)

    # Convert non-serialisable types
    summary = {
        k: (
            float(v) if hasattr(v, "__float__") and not isinstance(v, (str, bool))
            else v
        )
        for k, v in summary_raw.items()
        if k != "dry_spells"
    }

    sim = storage_simulation(
        df_scenario, buildings, req.tank_liters, req.population,
        req.usage_level, req.efficiency,
    )

    simulation_series = [
        SimulationRow(
            date=row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"]),
            precipitation_mm=float(row["precipitation_mm"]),
            tank_pct=float(row["tank_pct"]),
            tank_level_liters=float(row["tank_level_liters"]),
            days_remaining=float(row["days_remaining"]) if row["days_remaining"] != float("inf") else 9999.0,
        )
        for _, row in sim.iterrows()
    ]

    dry_spells_df = find_dry_spells(df_scenario)
    dry_spells = [
        DrySpell(
            start=row["start"].strftime("%Y-%m-%d"),
            end=row["end"].strftime("%Y-%m-%d"),
            days=int(row["days"]),
            total_rain_mm=float(row["total_rain_mm"]),
        )
        for _, row in dry_spells_df.iterrows()
    ] if not dry_spells_df.empty else []

    scenario_comparison = None
    if req.climate_scenario != "historical":
        comparison = compare_scenarios(df)
        scenario_comparison = [
            ScenarioComparison(**c) for c in comparison
        ]

    outcomes_raw = yearly_outcomes(
        df_full_scenario, buildings, req.tank_liters,
        req.population, req.usage_level, req.efficiency,
    )
    yearly_outcomes_list = [YearlyOutcome(**row) for row in outcomes_raw]

    return BeredskapsResponse(
        summary=summary,
        simulation_series=simulation_series,
        dry_spells=dry_spells,
        scenario_comparison=scenario_comparison,
        yearly_outcomes=yearly_outcomes_list,
    )
