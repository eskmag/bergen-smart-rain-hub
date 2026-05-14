"""Investment analysis for the rainwater + bergvarme integrated system.

Phase 5 module. Computes installation cost, annual savings, and lifecycle
metrics (payback, cumulative savings, NPV) for the full system: tank +
heat exchanger + piping + controls. Reuses `backend.economics.lifecycle_cost`
for the cost side rather than reimplementing.

All amounts in NOK. Per-unit prices are 2024-vintage Norwegian estimates.
"""

from backend.economics import lifecycle_cost


INSTALLATION_UNIT_COSTS = {
    "tank_per_liter": 8,             # NOK/L (nedgravd betong/HDPE, levert + installert)
    "heat_exchanger": 25_000,        # NOK, varmeveksler + tilkobling bergvarme
    "pump_and_controls": 15_000,     # NOK, sirkulasjonspumpe + styringssystem
    "piping_per_m2_roof": 150,       # NOK/m² takareal (takrenner + samlerør)
    "installation_labor": 40_000,    # NOK, grunnleggende rørlegger/elektriker
    "electricity_price_kwh": 1.20,   # NOK/kWh (2024-estimat)
    "maintenance_annual_pct": 0.02,  # 2 % av kapital årlig
    "water_price_per_liter": 0.015,  # NOK/L (kommunalt vann + avløp)
    "cooling_value_per_kwh": 0.80,   # NOK/kWh ekvivalent for unngått aktiv AC-strøm
}


def installation_cost(tank_capacity_liters, roof_area_m2,
                      unit_costs=None):
    """Itemised capex breakdown.

    Returns dict with keys: tank, heat_exchanger, pump_and_controls,
    piping, labor, total.
    """
    p = unit_costs or INSTALLATION_UNIT_COSTS
    items = {
        "tank": tank_capacity_liters * p["tank_per_liter"],
        "heat_exchanger": p["heat_exchanger"],
        "pump_and_controls": p["pump_and_controls"],
        "piping": roof_area_m2 * p["piping_per_m2_roof"],
        "labor": p["installation_labor"],
    }
    items["total"] = sum(items.values())
    return items


def annual_savings(annual_water_liters, annual_cooling_kwh,
                   annual_electricity_saved_kwh,
                   electricity_price_kwh=None,
                   water_price_per_liter=None,
                   cooling_value_per_kwh=None):
    """Itemised annual savings.

    Returns dict with: water, cooling, electricity, total.

    `annual_electricity_saved_kwh` is the heat-pump electricity reduction
    when rainwater is used as a warmer source than berg.
    `annual_cooling_kwh` is the passive-cooling load met without active AC,
    valued at `cooling_value_per_kwh`.
    """
    p = INSTALLATION_UNIT_COSTS
    elec_price = electricity_price_kwh if electricity_price_kwh is not None else p["electricity_price_kwh"]
    water_price = water_price_per_liter if water_price_per_liter is not None else p["water_price_per_liter"]
    cool_price = cooling_value_per_kwh if cooling_value_per_kwh is not None else p["cooling_value_per_kwh"]

    items = {
        "water": annual_water_liters * water_price,
        "cooling": annual_cooling_kwh * cool_price,
        "electricity": annual_electricity_saved_kwh * elec_price,
    }
    items["total"] = sum(items.values())
    return items


def investment_analysis(tank_capacity_liters, roof_area_m2,
                        annual_water_liters, annual_cooling_kwh,
                        annual_electricity_saved_kwh,
                        years=20,
                        electricity_price_kwh=None,
                        water_price_per_liter=None,
                        cooling_value_per_kwh=None,
                        maintenance_annual_pct=None):
    """Full investment analysis combining capex, opex, and savings.

    Reuses `backend.economics.lifecycle_cost` for the cost side
    (capital + annual maintenance × years).

    Returns dict with:
        capex: itemised dict from installation_cost
        savings: itemised dict from annual_savings
        annual_savings_total: NOK/year (savings - maintenance)
        annual_savings_gross: NOK/year (savings before maintenance)
        annual_maintenance: NOK/year
        cumulative_savings: list[float], length years+1, year 0 = -capex
        payback_years: float or None (None if savings never cover capex)
        npv: float — undiscounted (cumulative net cash flow at year `years`)
        years: int (echoed)
    """
    p = INSTALLATION_UNIT_COSTS
    maint_pct = maintenance_annual_pct if maintenance_annual_pct is not None else p["maintenance_annual_pct"]

    capex = installation_cost(tank_capacity_liters, roof_area_m2)
    savings = annual_savings(
        annual_water_liters, annual_cooling_kwh, annual_electricity_saved_kwh,
        electricity_price_kwh=electricity_price_kwh,
        water_price_per_liter=water_price_per_liter,
        cooling_value_per_kwh=cooling_value_per_kwh,
    )
    annual_maintenance = capex["total"] * maint_pct
    annual_net = savings["total"] - annual_maintenance

    cumulative = [-capex["total"]]
    for _ in range(years):
        cumulative.append(cumulative[-1] + annual_net)

    payback = None
    for i, val in enumerate(cumulative):
        if val >= 0 and i > 0:
            # Linear interpolation between i-1 and i
            prev = cumulative[i - 1]
            payback = (i - 1) + (-prev / (val - prev)) if val != prev else float(i)
            break

    # Total cost over years using the existing lifecycle_cost helper (capex + maintenance × years).
    total_lifecycle_cost = lifecycle_cost(capex["total"], annual_maintenance, years)

    return {
        "capex": capex,
        "savings": savings,
        "annual_savings_gross": savings["total"],
        "annual_maintenance": annual_maintenance,
        "annual_savings_total": annual_net,
        "cumulative_savings": cumulative,
        "payback_years": payback,
        "npv": cumulative[-1],
        "total_lifecycle_cost": total_lifecycle_cost,
        "years": years,
    }
