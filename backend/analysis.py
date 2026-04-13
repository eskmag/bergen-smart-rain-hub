from dataclasses import dataclass, field

import pandas as pd
import numpy as np

G = 9.81  # gravitational acceleration (m/s²)

# --- Emergency water needs (WHO / Norwegian standards) ---
WATER_NEEDS = {
    "drinking": 3.0,       # liters/person/day — WHO survival minimum
    "sanitation": 6.0,     # liters/person/day — basic hygiene
    "cooking": 3.0,        # liters/person/day
    "medical": 1.0,        # liters/person/day — wound cleaning etc.
    "survival_total": 13.0,  # liters/person/day — WHO emergency minimum
    "normal_usage": 150.0, # liters/person/day — Norwegian average
}

EMISSION_FACTORS = {
    "NO": 11,    # Norway: ~11 g CO₂/kWh (hydro-dominated grid)
    "EU": 250,   # EU average: ~250 g CO₂/kWh
}

SEASONS = {
    12: "Vinter (DJF)", 1: "Vinter (DJF)", 2: "Vinter (DJF)",
    3: "Vår (MAM)", 4: "Vår (MAM)", 5: "Vår (MAM)",
    6: "Sommer (JJA)", 7: "Sommer (JJA)", 8: "Sommer (JJA)",
    9: "Høst (SON)", 10: "Høst (SON)", 11: "Høst (SON)",
}


@dataclass
class Building:
    name: str
    roof_area_m2: float
    height_m: float = 5.0


@dataclass
class Community:
    name: str
    buildings: list = field(default_factory=list)
    population: int = 0
    tank_capacity_liters: float = 0.0


# ============================================================
# Water collection (core calculation)
# ============================================================

def water_collected(mm_rain, roof_area_m2, collection_efficiency=0.85):
    """Calculate liters collected from a roof. Default 85% efficiency
    accounts for first-flush diversion, guttering losses, and evaporation."""
    return mm_rain * roof_area_m2 * collection_efficiency


def daily_collection(df, buildings, collection_efficiency=0.85):
    """Calculate daily water collection for each building."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    rows = []
    for _, day in df.iterrows():
        for b in buildings:
            liters = water_collected(
                day["precipitation_mm"], b.roof_area_m2, collection_efficiency
            )
            rows.append({
                "date": day["date"],
                "building": b.name,
                "roof_area_m2": b.roof_area_m2,
                "precipitation_mm": day["precipitation_mm"],
                "liters": liters,
            })

    return pd.DataFrame(rows)


# ============================================================
# Emergency supply modeling
# ============================================================

def emergency_supply_days(total_liters, population, usage_level="survival_total"):
    """How many days can a population survive on stored water?"""
    daily_need = WATER_NEEDS[usage_level] * population
    if daily_need == 0:
        return 0
    return total_liters / daily_need


def storage_simulation(df, buildings, tank_capacity_liters, population,
                       usage_level="survival_total", collection_efficiency=0.85):
    """Simulate daily tank level: rainfall fills it, consumption drains it.
    Returns a DataFrame with daily tank state."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    daily_consumption = WATER_NEEDS[usage_level] * population
    total_roof_area = sum(b.roof_area_m2 for b in buildings)

    tank_level = tank_capacity_liters * 0.5  # assume tank starts half full
    rows = []

    for _, day in df.iterrows():
        inflow = water_collected(day["precipitation_mm"], total_roof_area, collection_efficiency)
        tank_level = min(tank_level + inflow, tank_capacity_liters)  # cap at tank size
        tank_level = max(tank_level - daily_consumption, 0)          # drain but not below 0

        rows.append({
            "date": day["date"],
            "precipitation_mm": day["precipitation_mm"],
            "inflow_liters": inflow,
            "consumption_liters": daily_consumption,
            "tank_level_liters": tank_level,
            "tank_pct": (tank_level / tank_capacity_liters * 100) if tank_capacity_liters > 0 else 0,
            "days_remaining": tank_level / daily_consumption if daily_consumption > 0 else float("inf"),
        })

    return pd.DataFrame(rows)


def find_dry_spells(df, min_days=3):
    """Find consecutive periods with < 1mm rainfall. These are the
    vulnerability windows for rainwater-dependent supply."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    df["dry"] = df["precipitation_mm"] < 1.0
    df["spell_id"] = (~df["dry"]).cumsum()

    spells = df[df["dry"]].groupby("spell_id").agg(
        start=("date", "first"),
        end=("date", "last"),
        days=("date", "count"),
        total_rain_mm=("precipitation_mm", "sum"),
    ).reset_index(drop=True)

    return spells[spells["days"] >= min_days].reset_index(drop=True)


def emergency_summary(df, buildings, tank_capacity_liters, population,
                      collection_efficiency=0.85):
    """Complete emergency preparedness assessment."""
    collection = daily_collection(df, buildings, collection_efficiency)
    total_collected = collection["liters"].sum()
    total_roof_area = sum(b.roof_area_m2 for b in buildings)

    sim = storage_simulation(
        df, buildings, tank_capacity_liters, population,
        "survival_total", collection_efficiency
    )

    dry_spells = find_dry_spells(df)
    longest_dry = int(dry_spells["days"].max()) if not dry_spells.empty else 0

    days_empty = int((sim["tank_level_liters"] == 0).sum())
    min_tank = sim["tank_level_liters"].min()
    avg_days_remaining = sim["days_remaining"].replace(float("inf"), np.nan).mean()

    return {
        "total_collected_liters": total_collected,
        "total_collected_m3": total_collected / 1000,
        "annual_per_person_liters": total_collected / population if population > 0 else 0,
        "days_of_survival_supply": emergency_supply_days(total_collected, population, "survival_total"),
        "days_of_normal_supply": emergency_supply_days(total_collected, population, "normal_usage"),
        "tank_capacity_liters": tank_capacity_liters,
        "days_tank_empty": days_empty,
        "min_tank_level_liters": min_tank,
        "avg_days_remaining": avg_days_remaining,
        "longest_dry_spell_days": longest_dry,
        "dry_spells": dry_spells,
        "population": population,
        "total_roof_area_m2": total_roof_area,
    }


# ============================================================
# Rainfall patterns
# ============================================================

def monthly_summary(df):
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M")

    summary = df.groupby("month")["precipitation_mm"].agg(
        total_mm="sum",
        mean_mm="mean",
        max_mm="max",
        rainy_days=lambda x: (x > 0.1).sum(),
    ).reset_index()

    summary["month"] = summary["month"].astype(str)
    return summary


def seasonal_summary(df):
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["season"] = df["date"].dt.month.map(SEASONS)

    summary = df.groupby("season")["precipitation_mm"].agg(
        total_mm="sum",
        mean_mm="mean",
        days="count",
    ).reset_index()

    return summary


# ============================================================
# Energy analysis (secondary)
# ============================================================

def calculate_rain_energy(mm_rain, roof_area_m2, height_m):
    liters = mm_rain * roof_area_m2
    mass_kg = liters  # 1 liter water = 1 kg

    energy_joules = mass_kg * G * height_m
    energy_wh = energy_joules / 3600

    return liters, energy_wh


def co2_offset(energy_wh):
    energy_kwh = energy_wh / 1000
    return {
        grid: energy_kwh * factor
        for grid, factor in EMISSION_FACTORS.items()
    }


def practical_equivalents(energy_wh):
    return {
        "phone_charges": energy_wh / 10,
        "led_bulb_hours": energy_wh / 7,
        "laptop_charges": energy_wh / 50,
        "electric_bike_km": energy_wh / 15,
    }


if __name__ == "__main__":
    buildings = [
        Building("Enebolig", roof_area_m2=100),
        Building("Blokk", roof_area_m2=400),
    ]

    # Simulate a rainy day
    rain_mm = 15
    for b in buildings:
        liters = water_collected(rain_mm, b.roof_area_m2)
        print(f"{b.name}: {liters:,.0f} liter fra {rain_mm} mm regn")

    # Emergency context
    population = 50
    tank = 10_000  # 10 m³ tank
    total = sum(water_collected(rain_mm, b.roof_area_m2) for b in buildings)
    days = emergency_supply_days(total, population)
    print(f"\nMed {total:,.0f} L og {population} personer: {days:.1f} dager beredskapsforsyning")
