from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from backend.analysis import (
    BERGEN_ANNUAL_RAINFALL_MM,
    DEFAULT_BUILDING_HEIGHT_M,
    DEFAULT_COLLECTION_EFFICIENCY,
    TANK_RECOMMENDATION_DAYS,
)


# ── Config ──────────────────────────────────────────────────────────────────

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


class BeredskapsResponse(BaseModel):
    summary: dict[str, Any]
    simulation_series: list[SimulationRow]
    dry_spells: list[DrySpell]
    scenario_comparison: list[ScenarioComparison] | None = None


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
