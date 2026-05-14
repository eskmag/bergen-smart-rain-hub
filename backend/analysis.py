from dataclasses import dataclass, field
import math

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

# --- Locked emergency reserve for energy modules (Phase 5) ---
EMERGENCY_RESERVE_DAYS = 7
EMERGENCY_RESERVE_PCT = 0.25

# Bergen Florida (SN50540) monthly air-temperature normals (°C)
BERGEN_AIR_TEMP_NORMALS = {
    1: 1.5, 2: 1.8, 3: 4.5, 4: 7.5, 5: 12.0, 6: 15.0,
    7: 17.0, 8: 16.5, 9: 13.0, 10: 9.0, 11: 5.0, 12: 2.5,
}

BERGEN_AIR_TEMP_ANNUAL_MEAN = sum(BERGEN_AIR_TEMP_NORMALS.values()) / 12

COOLING_CONFIG = {
    "floor_area_per_roof_m2": 0.8,
    "delta_t_floor": 4.0,                 # K, gulvkrets inn/ut
    "specific_heat_water": 4186,          # J/(kg·K)
    "passive_cooling_cop_factor": 15.0,   # ratio passive vs active AC
    "critical_tank_temp_c": 16.0,
    "default_room_temp_c": 23.0,
    "cooling_season_air_temp_c": 14.0,    # day counts as cooling-relevant when air > this (Norwegian summer)
}

HEAT_PUMP_CONFIG = {
    "default_delivery_temp_c": 35.0,    # gulvvarme; 60°C for radiatorer
    "carnot_efficiency": 0.45,
    "berg_temp_c_default": 7.0,
    "annual_demand_kwh_default": 50_000,
    "heating_season_air_temp_c": 15.0,  # day counts as heating-relevant when air < this
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


# Norwegian building presets: (label, roof_area_m2, default_people, height_m, description)
BUILDING_PRESETS = {
    "enebolig": {
        "label": "Enebolig",
        "roof_area_m2": 120,
        "default_people": 4,
        "height_m": 6,
        "description": "Frittstående hus med eget tak, typisk 100–150 m².",
    },
    "rekkehus": {
        "label": "Rekkehus",
        "roof_area_m2": 80,
        "default_people": 3,
        "height_m": 6,
        "description": "Rekke- eller kjedehus, din andel av taket er ca. 70–100 m².",
    },
    "leilighet_liten": {
        "label": "Leilighet (liten blokk)",
        "roof_area_m2": 300,
        "default_people": 20,
        "height_m": 12,
        "description": "Liten boligblokk med 6–10 leiligheter, felles tak ca. 250–400 m².",
    },
    "leilighet_stor": {
        "label": "Leilighet (stor blokk)",
        "roof_area_m2": 800,
        "default_people": 60,
        "height_m": 20,
        "description": "Stor boligblokk med 20+ leiligheter, felles tak ca. 600–1000 m².",
    },
    "barneskole": {
        "label": "Barneskole",
        "roof_area_m2": 800,
        "default_people": 200,
        "height_m": 8,
        "description": "Typisk barneskole med 150–300 elever og ansatte.",
    },
    "kontorbygg": {
        "label": "Kontorbygg",
        "roof_area_m2": 1200,
        "default_people": 150,
        "height_m": 15,
        "description": "Mellomstort kontorbygg med 100–200 ansatte.",
    },
    "idrettshall": {
        "label": "Idrettshall / gymsal",
        "roof_area_m2": 2000,
        "default_people": 300,
        "height_m": 10,
        "description": "Stor idrettshall — stort takflate gir mye oppsamling.",
    },
    "kjopesenter": {
        "label": "Kjøpesenter",
        "roof_area_m2": 3000,
        "default_people": 500,
        "height_m": 12,
        "description": "Kjøpesenter eller stormarked med svært stor takflate.",
    },
}


def recommend_tank_size(annual_liters, population, target_dry_days=30):
    """Recommend a tank size that covers a target number of dry days
    at survival consumption level. Returns a list of options."""
    daily_need = WATER_NEEDS["survival_total"] * population
    base_tank = daily_need * target_dry_days

    options = [
        {
            "label": "Minimum",
            "liters": round(daily_need * 7 / 100) * 100,
            "days_covered": 7,
            "description": "Dekker 1 uke uten nedbør",
        },
        {
            "label": "Anbefalt",
            "liters": round(base_tank / 100) * 100,
            "days_covered": target_dry_days,
            "description": f"Dekker {target_dry_days} dager uten nedbør",
        },
        {
            "label": "Robust",
            "liters": round(daily_need * 60 / 100) * 100,
            "days_covered": 60,
            "description": "Dekker 2 måneder uten nedbør",
        },
    ]

    return options


# ============================================================
# Locked emergency reserve (Phase 5)
# ============================================================

def emergency_reserve_liters(tank_capacity_liters, population,
                             reserve_days=EMERGENCY_RESERVE_DAYS,
                             reserve_pct=EMERGENCY_RESERVE_PCT):
    """Locked emergency reserve. Energy modules may not consume below this.

    Reserve = max(reserve_days × daily_survival_need, reserve_pct × tank_capacity),
    capped at tank_capacity (cannot lock more than the tank holds).
    """
    if tank_capacity_liters <= 0:
        return 0.0
    days_floor = WATER_NEEDS["survival_total"] * max(0, population) * reserve_days
    pct_floor = tank_capacity_liters * reserve_pct
    return min(tank_capacity_liters, max(days_floor, pct_floor))


def available_volume(tank_level_liters, tank_capacity_liters, population,
                     reserve_days=EMERGENCY_RESERVE_DAYS,
                     reserve_pct=EMERGENCY_RESERVE_PCT):
    """Disponibelt volum over beredskapsgrensen. Aldri under 0."""
    reserve = emergency_reserve_liters(
        tank_capacity_liters, population, reserve_days, reserve_pct
    )
    return max(0.0, tank_level_liters - reserve)


# ============================================================
# Tank temperature model (Phase 5)
# ============================================================

def estimate_tank_temperature(month, tank_type="nedgravd"):
    """Estimated tank water temperature (°C) for the given month.

    nedgravd (buried): sinusoid around the annual mean (~8.8°C for Bergen)
        with ±2°C swing, lagging two months behind air temp (coldest March,
        warmest September).
    overflate (above-ground): tracks monthly air temp with 0.7× damping
        and a +3°C offset from soil/structure thermal mass.

    Falls back to BERGEN_AIR_TEMP_NORMALS for the air-temp component;
    Section 5.2 swaps in real Frost data when available.
    """
    if month not in BERGEN_AIR_TEMP_NORMALS:
        raise ValueError(f"month must be 1-12, got {month}")
    air_temp = BERGEN_AIR_TEMP_NORMALS[month]

    if tank_type == "nedgravd":
        # Coldest March, warmest September → 6-month phase (Sept = peak)
        phase_offset = (month - 9) * (2 * math.pi / 12)
        return BERGEN_AIR_TEMP_ANNUAL_MEAN + 2.0 * math.cos(phase_offset)
    if tank_type == "overflate":
        return air_temp * 0.7 + 3.0
    raise ValueError(f"tank_type must be 'nedgravd' or 'overflate', got {tank_type!r}")


def tank_temperature_series(df, tank_type="nedgravd"):
    """Per-day tank temperature aligned to df['date']."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    return df["date"].dt.month.map(lambda m: estimate_tank_temperature(m, tank_type))


# ============================================================
# Passive cooling (Phase 5)
# ============================================================

def passive_cooling_potential(tank_temp_c, room_temp_c,
                              available_liters, floor_area_m2):
    """One day's passive cooling potential.

    Returns 0 cooling when tank is too warm (>= critical_tank_temp_c) or there
    is no temperature delta. Mass moved per day is capped to a realistic
    circulation: floor_area × 2 kg/m² (about 2 mm of water depth equivalent),
    further limited by available_liters.
    """
    delta_t = room_temp_c - tank_temp_c
    if delta_t <= 0 or tank_temp_c >= COOLING_CONFIG["critical_tank_temp_c"]:
        return {
            "cooling_possible": False,
            "cooling_kwh": 0.0,
            "cooling_w": 0.0,
            "tank_temp_c": tank_temp_c,
            "delta_t": max(0.0, delta_t),
        }

    mass_kg = min(available_liters, floor_area_m2 * 2.0)
    if mass_kg <= 0:
        return {
            "cooling_possible": False,
            "cooling_kwh": 0.0,
            "cooling_w": 0.0,
            "tank_temp_c": tank_temp_c,
            "delta_t": delta_t,
        }

    energy_joules = mass_kg * COOLING_CONFIG["specific_heat_water"] * delta_t
    cooling_kwh = energy_joules / 3_600_000
    return {
        "cooling_possible": True,
        "cooling_kwh": cooling_kwh,
        "cooling_w": energy_joules / (3600 * 8),  # spread over 8-hour day
        "tank_temp_c": tank_temp_c,
        "delta_t": delta_t,
    }


def annual_cooling_simulation(df, buildings, tank_capacity_liters, population,
                              tank_type="nedgravd",
                              room_temp_c=None,
                              floor_area_m2=None,
                              collection_efficiency=0.85,
                              reserve_days=EMERGENCY_RESERVE_DAYS,
                              reserve_pct=EMERGENCY_RESERVE_PCT):
    """Simulate daily cooling potential over the year.

    Cooling is enabled on days where the tank is below critical_tank_temp_c
    AND outside air temperature is above cooling_season_air_temp_c (proxy for
    actual cooling demand). Volume is constrained to `available_liters` from
    the underlying storage simulation, so the locked emergency reserve is
    never tapped.

    Returns a DataFrame with columns: date, air_temp_c, tank_temp_c,
    available_liters, cooling_kwh, cooling_active.
    """
    if room_temp_c is None:
        room_temp_c = COOLING_CONFIG["default_room_temp_c"]

    total_roof_area = sum(b.roof_area_m2 for b in buildings)
    if floor_area_m2 is None:
        floor_area_m2 = total_roof_area * COOLING_CONFIG["floor_area_per_roof_m2"]

    sim = storage_simulation(
        df, buildings, tank_capacity_liters, population,
        collection_efficiency=collection_efficiency,
        reserve_days=reserve_days, reserve_pct=reserve_pct,
    )
    sim["date"] = pd.to_datetime(sim["date"])

    tank_temps = sim["date"].dt.month.map(
        lambda m: estimate_tank_temperature(m, tank_type)
    )

    # Air temperature: use real data if present, else fall back to monthly normals.
    df_in = df.copy()
    df_in["date"] = pd.to_datetime(df_in["date"])
    if "air_temperature_c" in df_in.columns:
        air_lookup = dict(zip(df_in["date"], df_in["air_temperature_c"]))
    else:
        air_lookup = {}
    air_temps = sim["date"].map(
        lambda d: air_lookup.get(d) if pd.notna(air_lookup.get(d, float("nan")))
        else BERGEN_AIR_TEMP_NORMALS[d.month]
    )

    cooling_threshold = COOLING_CONFIG["cooling_season_air_temp_c"]

    rows = []
    for idx in range(len(sim)):
        date = sim.iloc[idx]["date"]
        tank_temp = float(tank_temps.iloc[idx])
        air_temp = float(air_temps.iloc[idx])
        available = float(sim.iloc[idx]["available_liters"])

        if air_temp <= cooling_threshold:
            # outside cooling season — no demand
            rows.append({
                "date": date, "air_temp_c": air_temp, "tank_temp_c": tank_temp,
                "available_liters": available, "cooling_kwh": 0.0,
                "cooling_active": False,
            })
            continue

        result = passive_cooling_potential(
            tank_temp, room_temp_c, available, floor_area_m2
        )
        rows.append({
            "date": date, "air_temp_c": air_temp, "tank_temp_c": tank_temp,
            "available_liters": available,
            "cooling_kwh": result["cooling_kwh"],
            "cooling_active": result["cooling_possible"],
        })

    return pd.DataFrame(rows)


# ============================================================
# Heat-pump supplement (Phase 5)
# ============================================================

def cop_estimate(source_temp_c, delivery_temp_c=None):
    """Estimate COP for a water-water heat pump.

    Carnot COP × practical efficiency (0.45 by default).
    """
    if delivery_temp_c is None:
        delivery_temp_c = HEAT_PUMP_CONFIG["default_delivery_temp_c"]
    if delivery_temp_c <= source_temp_c:
        # No useful work — heat pump only makes sense when delivering hotter
        # than the source. Return 1.0 as a sentinel (resistive heating fallback).
        return 1.0
    delivery_k = delivery_temp_c + 273.15
    source_k = source_temp_c + 273.15
    carnot = delivery_k / (delivery_k - source_k)
    return carnot * HEAT_PUMP_CONFIG["carnot_efficiency"]


def heat_pump_supplement_simulation(df, tank_temp_series=None,
                                    berg_temp_c=None,
                                    delivery_temp_c=None,
                                    annual_demand_kwh=None,
                                    tank_type="nedgravd"):
    """Per-day source choice and heat-pump electricity use.

    For each day in the heating season (air temp below threshold), the
    heat pump uses whichever source is warmer — rainwater tank or berg.
    Demand is distributed across heating days proportional to a simple
    degree-day approximation.

    Returns DataFrame with: date, air_temp_c, tank_temp_c, source,
    cop_used, kwh_demand, kwh_electricity, kwh_savings_vs_berg.
    """
    if berg_temp_c is None:
        berg_temp_c = HEAT_PUMP_CONFIG["berg_temp_c_default"]
    if delivery_temp_c is None:
        delivery_temp_c = HEAT_PUMP_CONFIG["default_delivery_temp_c"]
    if annual_demand_kwh is None:
        annual_demand_kwh = HEAT_PUMP_CONFIG["annual_demand_kwh_default"]

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    if tank_temp_series is None:
        tank_temp_series = tank_temperature_series(df, tank_type)
    tank_temp_series = pd.Series(list(tank_temp_series), index=df.index)

    if "air_temperature_c" in df.columns:
        air = df["air_temperature_c"].copy()
        # Fill missing with monthly normals
        for idx in air.index[air.isna()]:
            air.loc[idx] = BERGEN_AIR_TEMP_NORMALS[df.loc[idx, "date"].month]
    else:
        air = df["date"].dt.month.map(BERGEN_AIR_TEMP_NORMALS)

    heating_threshold = HEAT_PUMP_CONFIG["heating_season_air_temp_c"]
    # Degree-day weighting: weight ∝ max(0, threshold - air_temp).
    weight = (heating_threshold - air).clip(lower=0)
    total_weight = weight.sum()
    if total_weight > 0:
        daily_demand = annual_demand_kwh * weight / total_weight
    else:
        daily_demand = pd.Series([0.0] * len(df), index=df.index)

    rows = []
    for idx in df.index:
        date = df.loc[idx, "date"]
        tank_t = float(tank_temp_series.loc[idx])
        air_t = float(air.loc[idx])
        demand_kwh = float(daily_demand.loc[idx])

        if demand_kwh <= 0:
            rows.append({
                "date": date, "air_temp_c": air_t, "tank_temp_c": tank_t,
                "source": "none", "cop_used": 0.0, "kwh_demand": 0.0,
                "kwh_electricity": 0.0, "kwh_savings_vs_berg": 0.0,
            })
            continue

        # Pick warmer source (heat pump prefers warmer source for higher COP).
        if tank_t > berg_temp_c:
            source = "rainwater"
            source_temp = tank_t
        else:
            source = "berg"
            source_temp = berg_temp_c

        cop_used = cop_estimate(source_temp, delivery_temp_c)
        cop_berg = cop_estimate(berg_temp_c, delivery_temp_c)
        elec = demand_kwh / cop_used if cop_used > 0 else demand_kwh
        elec_berg = demand_kwh / cop_berg if cop_berg > 0 else demand_kwh
        savings = max(0.0, elec_berg - elec)

        rows.append({
            "date": date, "air_temp_c": air_t, "tank_temp_c": tank_t,
            "source": source, "cop_used": cop_used,
            "kwh_demand": demand_kwh, "kwh_electricity": elec,
            "kwh_savings_vs_berg": savings,
        })

    return pd.DataFrame(rows)


def annual_cop_improvement(tank_temp_series, berg_temp_c=None,
                           delivery_temp_c=None):
    """Mean COP with rainwater-priority strategy vs berg-only baseline.

    Returns dict with cop_baseline, cop_with_rainwater, cop_uplift,
    rainwater_dominant_days (days where tank > berg).
    """
    if berg_temp_c is None:
        berg_temp_c = HEAT_PUMP_CONFIG["berg_temp_c_default"]
    if delivery_temp_c is None:
        delivery_temp_c = HEAT_PUMP_CONFIG["default_delivery_temp_c"]

    cop_baseline = cop_estimate(berg_temp_c, delivery_temp_c)
    chosen_temps = [max(t, berg_temp_c) for t in tank_temp_series]
    cops = [cop_estimate(t, delivery_temp_c) for t in chosen_temps]
    cop_with = sum(cops) / len(cops) if cops else 0.0
    rainwater_days = sum(1 for t in tank_temp_series if t > berg_temp_c)

    return {
        "cop_baseline": cop_baseline,
        "cop_with_rainwater": cop_with,
        "cop_uplift": cop_with - cop_baseline,
        "rainwater_dominant_days": rainwater_days,
    }


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
                       usage_level="survival_total", collection_efficiency=0.85,
                       reserve_days=EMERGENCY_RESERVE_DAYS,
                       reserve_pct=EMERGENCY_RESERVE_PCT):
    """Simulate daily tank level: rainfall fills it, consumption drains it.
    Returns a DataFrame with daily tank state.

    `available_liters` is the volume above the locked emergency reserve
    (`max(reserve_days × daily_need, reserve_pct × tank_capacity)`), available
    for energy or cooling uses.
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    daily_consumption = WATER_NEEDS[usage_level] * population
    total_roof_area = sum(b.roof_area_m2 for b in buildings)

    reserve = emergency_reserve_liters(
        tank_capacity_liters, population, reserve_days, reserve_pct
    )

    tank_level = tank_capacity_liters * 0.5  # assume tank starts half full
    rows = []

    for _, day in df.iterrows():
        inflow = water_collected(day["precipitation_mm"], total_roof_area, collection_efficiency)
        tank_level = min(tank_level + inflow, tank_capacity_liters)  # cap at tank size
        tank_level = max(tank_level - daily_consumption, 0)          # drain but not below 0

        available = max(0, tank_level - reserve)
        rows.append({
            "date": day["date"],
            "precipitation_mm": day["precipitation_mm"],
            "inflow_liters": inflow,
            "consumption_liters": daily_consumption,
            "tank_level_liters": tank_level,
            "tank_pct": (tank_level / tank_capacity_liters * 100) if tank_capacity_liters > 0 else 0,
            "days_remaining": tank_level / daily_consumption if daily_consumption > 0 else float("inf"),
            "available_liters": available,
            "available_pct": (available / tank_capacity_liters * 100) if tank_capacity_liters > 0 else 0,
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
