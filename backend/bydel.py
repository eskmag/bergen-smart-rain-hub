"""Bydel-level aggregation of rainwater harvesting potential.

Policy view: what share of Bergen's emergency water demand (WHO survival
minimum) could distributed rooftop harvesting cover per bydel?

DATA QUALITY NOTE — the per-bydel roof areas are first-order estimates:
population × SUITABLE_ROOF_M2_PER_CAPITA, where the per-capita factor is a
documented assumption (suitable, structurally accessible roof area per
resident, conservative for dense bydeler). Replacing these with FKB-bygning
(Kartverket) footprints is recorded as future work in the phase report.
Population figures: SSB, Bergen kommune bydelsfakta (2024, rounded).
"""

from backend.analysis import (
    WATER_NEEDS, DEFAULT_COLLECTION_EFFICIENCY, BERGEN_ANNUAL_RAINFALL_MM,
)

# Conservative suitable-roof estimate per resident (m²). Documented assumption.
SUITABLE_ROOF_M2_PER_CAPITA = 18.0
# Dense urban bydeler get a reduction factor (more apartment blocks, shared roofs).
_DENSITY_FACTOR = {"bergenhus": 0.6, "arstad": 0.7}

BYDELER = {
    "arna":          {"label": "Arna",          "population": 28_000},
    "bergenhus":     {"label": "Bergenhus",     "population": 46_000},
    "fana":          {"label": "Fana",          "population": 45_000},
    "fyllingsdalen": {"label": "Fyllingsdalen", "population": 30_000},
    "laksevag":      {"label": "Laksevåg",      "population": 41_000},
    "ytrebygda":     {"label": "Ytrebygda",     "population": 30_000},
    "arstad":        {"label": "Årstad",        "population": 42_000},
    "asane":         {"label": "Åsane",         "population": 43_000},
}


def suitable_roof_m2(bydel_key):
    b = BYDELER[bydel_key]
    factor = _DENSITY_FACTOR.get(bydel_key, 1.0)
    return b["population"] * SUITABLE_ROOF_M2_PER_CAPITA * factor


def city_potential(participation_pct=0.20,
                   annual_rainfall_mm=BERGEN_ANNUAL_RAINFALL_MM,
                   efficiency=DEFAULT_COLLECTION_EFFICIENCY):
    """Daily average yield vs. WHO-minimum emergency demand, per bydel.

    participation_pct: share of suitable roof area actually connected.
    """
    if not 0.0 < participation_pct <= 1.0:
        raise ValueError("participation_pct must be in (0, 1]")

    daily_mm = annual_rainfall_mm / 365.0
    need = WATER_NEEDS["survival_total"]

    rows = []
    for key, b in BYDELER.items():
        roof = suitable_roof_m2(key) * participation_pct
        daily_yield = daily_mm * roof * efficiency  # liters/day (mm == L/m²)
        demand = b["population"] * need
        rows.append({
            "key": key,
            "label": b["label"],
            "population": b["population"],
            "suitable_roof_m2": round(suitable_roof_m2(key)),
            "daily_yield_liters": round(daily_yield),
            "demand_liters": round(demand),
            "coverage_pct": round(100 * daily_yield / demand, 1),
        })

    total_yield = sum(r["daily_yield_liters"] for r in rows)
    total_demand = sum(r["demand_liters"] for r in rows)
    return {
        "bydeler": rows,
        "participation_pct": participation_pct,
        "total_daily_liters": total_yield,
        "total_demand_liters": total_demand,
        "demand_coverage_pct": round(100 * total_yield / total_demand, 1),
        # How many people the average daily yield would sustain at WHO minimum
        "persons_covered": round(total_yield / need),
        # Expose the core roof assumption so the frontend never hardcodes it
        "roof_m2_per_capita": SUITABLE_ROOF_M2_PER_CAPITA,
        "assumptions": [
            f"Egnet takareal: {SUITABLE_ROOF_M2_PER_CAPITA:.0f} m² per innbygger "
            "(reduksjonsfaktor for tette bydeler)",
            f"Normalnedbør {annual_rainfall_mm} mm/år, jevnt fordelt (årsgjennomsnitt)",
            f"Systemvirkningsgrad {efficiency:.0%}",
            f"Behov: WHO overlevelsesminimum {need:.0f} L/person/dag",
        ],
    }
