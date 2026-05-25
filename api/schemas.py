from __future__ import annotations

from typing import Any

from pydantic import BaseModel


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


class ConfigResponse(BaseModel):
    scales: list[ScaleSchema]
    scale_presets: dict[str, list[str]]
    building_presets: list[BuildingPreset]
    infrastructure_facilities: list[InfrastructureFacility]
    climate_scenarios: list[ClimateScenario]
    water_needs: dict[str, float]


# ── Observations ─────────────────────────────────────────────────────────────

class Observation(BaseModel):
    date: str
    precipitation_mm: float
    air_temperature_c: float | None = None


# ── Quick simulation ──────────────────────────────────────────────────────────

class QuickSimRequest(BaseModel):
    roof_area_m2: float
    population: int
    total_precipitation_mm: float


class TankOption(BaseModel):
    label: str
    liters: int
    days_covered: int
    description: str


class QuickSimResponse(BaseModel):
    annual_liters: float
    supply_days: float
    verdict: str
    color: str
    metrics: dict[str, Any]
    tank_options: list[TankOption]


# ── Beredskap simulation ──────────────────────────────────────────────────────

class BuildingInput(BaseModel):
    label: str
    roof_area_m2: float
    height_m: float = 5.0


class BeredskapsRequest(BaseModel):
    buildings: list[BuildingInput]
    tank_liters: int
    population: int
    efficiency: float = 0.85
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


# ── Risk assessment ───────────────────────────────────────────────────────────

class RiskAssessRequest(BaseModel):
    tank_liters: int
    population: int
    roof_area_m2: float
    scale: str = "household"
    days_tank_empty: float = 0
    longest_dry_spell: int = 0


class AssessedRisk(BaseModel):
    name: str
    category: str
    likelihood: str
    impact: str
    overall: str
    mitigation: str
    score: int
    reason: str


class CCP(BaseModel):
    id: str
    name: str
    description: str
    control_measure: str


class RiskAssessResponse(BaseModel):
    assessed_risks: list[AssessedRisk]
    ccps: list[CCP]
    category_labels: dict[str, str]


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
