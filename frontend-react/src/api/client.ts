// Typed API client — all fetch calls live here.
//
// Types are generated from the FastAPI OpenAPI spec. To regenerate after a
// backend schema change:
//   python scripts/export_openapi.py frontend-react/openapi.json
//   cd frontend-react && npm run generate:api

import type { components } from './schema'

export type YearlyOutcome = components['schemas']['YearlyOutcome']
export type ScaleSchema = components['schemas']['ScaleSchema']
export type BuildingPreset = components['schemas']['BuildingPreset']
export type InfrastructureFacility = components['schemas']['InfrastructureFacility']
export type ClimateScenario = components['schemas']['ClimateScenario']
export type ConfigDefaults = components['schemas']['ConfigDefaults']
export type ConfigResponse = components['schemas']['ConfigResponse']
export type Observation = components['schemas']['Observation']
export type BuildingInput = components['schemas']['BuildingInput']
export type BeredskapsRequest = components['schemas']['BeredskapsRequest']
export type SimulationRow = components['schemas']['SimulationRow']
export type DrySpell = components['schemas']['DrySpell']
export type ScenarioComparison = components['schemas']['ScenarioComparison']
export type BeredskapsResponse = components['schemas']['BeredskapsResponse']
export type CostEstimateRow = components['schemas']['CostEstimateRow']
export type CostBreakdownItem = components['schemas']['CostBreakdownItem']
export type CostsResponse = components['schemas']['CostsResponse']
export type RoofMaterial = components['schemas']['RoofMaterial']
export type TreatmentResponse = components['schemas']['TreatmentResponse']
export type StationSchema = components['schemas']['StationSchema']
export type BydelRow = components['schemas']['BydelRow']
export type BydelResponse = components['schemas']['BydelResponse']
export type EnergyResponse = components['schemas']['EnergyResponse']

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

  observations: (days = 365, station?: string) =>
    apiFetch<Observation[]>(
      `/api/observations?days=${days}${station ? `&station=${station}` : ''}`,
    ),

  simulateBeredskap: (req: BeredskapsRequest) =>
    apiFetch<BeredskapsResponse>('/api/simulate/beredskap', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    }),

  costs: (population: number, scale: string, annualLiters = 0) =>
    apiFetch<CostsResponse>(
      `/api/costs?population=${population}&scale=${scale}&annual_liters=${annualLiters}`,
    ),

  treatment: (material: string, scale: string) =>
    apiFetch<TreatmentResponse>(`/api/treatment?material=${material}&scale=${scale}`),

  bydel: (participation: number) =>
    apiFetch<BydelResponse>(`/api/bydel?participation=${participation}`),

  energy: (roofAreaM2: number, heightM: number) =>
    apiFetch<EnergyResponse>(`/api/energy?roof_area_m2=${roofAreaM2}&height_m=${heightM}`),
}
