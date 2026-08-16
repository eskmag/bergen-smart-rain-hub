from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from backend.analysis import (
    BERGEN_ANNUAL_RAINFALL_MM,
    DEFAULT_BUILDING_HEIGHT_M,
    DEFAULT_COLLECTION_EFFICIENCY,
    TANK_RECOMMENDATION_DAYS,
)
from backend.config import DEFAULT_STATION_ID


# ── Config ──────────────────────────────────────────────────────────────────

class StationSchema(BaseModel):
    id: str
    label: str
    note: str


class ScaleSchema(BaseModel):
    key: str
    label: str
    description: str
    typical_population: list[int]
    typical_tank_liters: list[int]
    typical_buildings: list[int]
    treatment_level: str
    governance_note: str
    cost_range_nok: list[int]


class BuildingPreset(BaseModel):
    key: str
    label: str
    roof_area_m2: int
    default_people: int
    height_m: float
    description: str


class InfrastructureFacility(BaseModel):
    key: str
    label: str
    roof_area_m2: int
    default_people: int
    height_m: float
    description: str


class ClimateScenario(BaseModel):
    key: str
    label: str
    description: str
    intensity_factor: float
    dry_spell_factor: float


class ConfigDefaults(BaseModel):
    """Shared domain defaults — the frontend reads these instead of
    hardcoding mirrors of backend constants."""
    collection_efficiency: float = DEFAULT_COLLECTION_EFFICIENCY
    building_height_m: float = DEFAULT_BUILDING_HEIGHT_M
    annual_rainfall_mm: float = BERGEN_ANNUAL_RAINFALL_MM
    tank_recommendation_days: list[int] = list(TANK_RECOMMENDATION_DAYS)
    station_id: str = DEFAULT_STATION_ID


class RoofMaterial(BaseModel):
    key: str
    label: str
    risk_class: str
    description: str


class ConfigResponse(BaseModel):
    scales: list[ScaleSchema]
    scale_presets: dict[str, list[str]]
    building_presets: list[BuildingPreset]
    infrastructure_facilities: list[InfrastructureFacility]
    climate_scenarios: list[ClimateScenario]
    water_needs: dict[str, float]
    defaults: ConfigDefaults
    roof_materials: list[RoofMaterial]
    stations: list[StationSchema]


# ── Observations ─────────────────────────────────────────────────────────────

class Observation(BaseModel):
    date: str
    precipitation_mm: float
    air_temperature_c: float | None = None


# ── Beredskap simulation ──────────────────────────────────────────────────────

class BuildingInput(BaseModel):
    name: str
    roof_area_m2: float
    height_m: float = DEFAULT_BUILDING_HEIGHT_M


class BeredskapsRequest(BaseModel):
    buildings: list[BuildingInput]
    tank_liters: int
    population: int
    efficiency: float = DEFAULT_COLLECTION_EFFICIENCY
    usage_level: str = "survival_total"
    climate_scenario: str = "historical"
    station: str = DEFAULT_STATION_ID


class SimulationRow(BaseModel):
    date: str
    precipitation_mm: float
    tank_pct: float
    tank_level_liters: float
    days_remaining: float


class DrySpell(BaseModel):
    start: str
    end: str
    days: int
    total_rain_mm: float


class ScenarioComparison(BaseModel):
    scenario: str
    label: str
    total_precip_mm: float
    dry_days: int
    longest_dry_spell: int


class YearlyOutcome(BaseModel):
    year: int
    total_collected_liters: float
    days_tank_empty: int
    min_tank_pct: float
    longest_dry_spell_days: int


class BeredskapsResponse(BaseModel):
    summary: dict[str, Any]
    simulation_series: list[SimulationRow]
    dry_spells: list[DrySpell]
    scenario_comparison: list[ScenarioComparison] | None = None
    yearly_outcomes: list[YearlyOutcome] = []


# ── Cost analysis ─────────────────────────────────────────────────────────────

class CostEstimateRow(BaseModel):
    label: str
    capital_low: int
    capital_high: int
    annual_operating_low: int
    annual_operating_high: int
    capacity_low: int
    capacity_high: int


class CostBreakdownItem(BaseModel):
    category: str
    amount: int


class CostsResponse(BaseModel):
    estimate_label: str
    capital_low: int
    capital_high: int
    annual_op_low: int
    annual_op_high: int
    capital: int
    annual_op: int
    cost_per_person: float
    lifecycle_10: int
    lifecycle_20: int
    lifecycle_30: int
    cost_per_liter_20: float | None
    capital_breakdown: list[CostBreakdownItem]
    operating_breakdown: list[CostBreakdownItem]
    all_estimates: list[CostEstimateRow]


# ── Water quality / treatment ────────────────────────────────────────────────

class TreatmentResponse(BaseModel):
    material: str
    material_label: str
    risk_class: str
    potable: bool
    barriers: list[str]
    cost_low_nok: int
    cost_high_nok: int
    note: str


# ── Bydel potential (policy view) ────────────────────────────────────────────

class BydelRow(BaseModel):
    key: str
    label: str
    population: int
    suitable_roof_m2: int
    daily_yield_liters: int
    demand_liters: int
    coverage_pct: float


class BydelResponse(BaseModel):
    bydeler: list[BydelRow]
    participation_pct: float
    total_daily_liters: int
    total_demand_liters: int
    demand_coverage_pct: float
    persons_covered: int
    roof_m2_per_capita: float
    assumptions: list[str]


# ── Energy (BKK angle) ───────────────────────────────────────────────────────

class EnergyResponse(BaseModel):
    annual_liters: float
    annual_energy_kwh: float
    co2_offset_g: dict[str, float]
    equivalents: dict[str, float]


# ── Validation (2018 dry-spring backtest) ────────────────────────────────────

class LongestSpell(BaseModel):
    days: int
    start: str | None
    end: str | None


class TankTier(BaseModel):
    label: str
    liters: int
    days_tank_empty: int
    min_tank_liters: int


class ValidationCase(BaseModel):
    roof_m2: int
    population: int
    efficiency: float


class ValidationResponse(BaseModel):
    station_id: str
    year: int
    total_rainfall_mm: float
    n_dry_spells: int
    longest_dry_spell: LongestSpell
    case: ValidationCase
    tiers: list[TankTier]
