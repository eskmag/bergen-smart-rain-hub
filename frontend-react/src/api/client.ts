// Typed API client — all fetch calls live here.

export interface ScaleSchema {
  key: string
  label: string
  description: string
  typical_population: number[]
  typical_tank_liters: number[]
  typical_buildings: number[]
  treatment_level: string
  governance_note: string
  cost_range_nok: number[]
}

export interface BuildingPreset {
  key: string
  label: string
  roof_area_m2: number
  default_people: number
  height_m: number
  description: string
}

export interface InfrastructureFacility {
  key: string
  label: string
  roof_area_m2: number
  default_people: number
  height_m: number
  description: string
}

export interface ClimateScenario {
  key: string
  label: string
  description: string
  intensity_factor: number
  dry_spell_factor: number
}

export interface ConfigResponse {
  scales: ScaleSchema[]
  scale_presets: Record<string, string[]>
  building_presets: BuildingPreset[]
  infrastructure_facilities: InfrastructureFacility[]
  climate_scenarios: ClimateScenario[]
  water_needs: Record<string, number>
}

export interface Observation {
  date: string
  precipitation_mm: number
  air_temperature_c: number | null
}

export interface TankOption {
  label: string
  liters: number
  days_covered: number
  description: string
}

export interface QuickSimRequest {
  roof_area_m2: number
  population: number
  total_precipitation_mm: number
}

export interface QuickSimResponse {
  annual_liters: number
  supply_days: number
  verdict: string
  color: string
  metrics: Record<string, number>
  tank_options: TankOption[]
}

export interface BuildingInput {
  label: string
  roof_area_m2: number
  height_m: number
}

export interface BeredskapsRequest {
  buildings: BuildingInput[]
  tank_liters: number
  population: number
  efficiency: number
  usage_level: string
  climate_scenario: string
}

export interface SimulationRow {
  date: string
  precipitation_mm: number
  tank_pct: number
  tank_level_liters: number
  days_remaining: number
}

export interface DrySpell {
  start: string
  end: string
  days: number
  total_rain_mm: number
}

export interface ScenarioComparison {
  scenario: string
  label: string
  total_precip_mm: number
  dry_days: number
  longest_dry_spell: number
}

export interface BeredskapsResponse {
  summary: Record<string, number>
  simulation_series: SimulationRow[]
  dry_spells: DrySpell[]
  scenario_comparison: ScenarioComparison[] | null
}

export interface AssessedRisk {
  name: string
  category: string
  likelihood: string
  impact: string
  overall: string
  mitigation: string
  score: number
  reason: string
}

export interface CCP {
  id: string
  name: string
  description: string
  control_measure: string
}

export interface RiskAssessRequest {
  tank_liters: number
  population: number
  roof_area_m2: number
  scale: string
  days_tank_empty: number
  longest_dry_spell: number
}

export interface RiskAssessResponse {
  assessed_risks: AssessedRisk[]
  ccps: CCP[]
  category_labels: Record<string, string>
}

export interface CostEstimateRow {
  label: string
  capital_low: number
  capital_high: number
  annual_operating_low: number
  annual_operating_high: number
  capacity_low: number
  capacity_high: number
}

export interface CostBreakdownItem {
  category: string
  amount: number
}

export interface CostsResponse {
  estimate_label: string
  capital_low: number
  capital_high: number
  annual_op_low: number
  annual_op_high: number
  capital: number
  annual_op: number
  cost_per_person: number
  lifecycle_10: number
  lifecycle_20: number
  lifecycle_30: number
  cost_per_liter_20: number | null
  capital_breakdown: CostBreakdownItem[]
  operating_breakdown: CostBreakdownItem[]
  all_estimates: CostEstimateRow[]
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${res.status}: ${text}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  config: () => apiFetch<ConfigResponse>('/api/config'),

  observations: (days = 365) =>
    apiFetch<Observation[]>(`/api/observations?days=${days}`),

  simulateQuick: (req: QuickSimRequest) =>
    apiFetch<QuickSimResponse>('/api/simulate/quick', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    }),

  simulateBeredskap: (req: BeredskapsRequest) =>
    apiFetch<BeredskapsResponse>('/api/simulate/beredskap', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    }),

  assessRisk: (req: RiskAssessRequest) =>
    apiFetch<RiskAssessResponse>('/api/assess/risk', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    }),

  costs: (population: number, scale: string, annualLiters = 0) =>
    apiFetch<CostsResponse>(
      `/api/costs?population=${population}&scale=${scale}&annual_liters=${annualLiters}`,
    ),
}
