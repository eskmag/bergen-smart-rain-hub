// Domain helpers for quick client-side estimates. Domain constants
// (rainfall, efficiency, water needs, tank tiers) come from /api/config —
// nothing load-bearing is hardcoded here.

import type { ConfigDefaults } from '../api/client'

// V (L) = A (m²) × R (mm) × C; mm/1000 → m³, ×1000 → L cancel out
export function annualCollectionLiters(roofM2: number, defaults: ConfigDefaults): number {
  return roofM2 * defaults.annual_rainfall_mm * defaults.collection_efficiency
}

// Days the annual harvest can supply: annualL / (people × L/person/day)
export function emergencyDays(annualL: number, people: number, lPerPersonPerDay: number): number {
  return Math.floor(annualL / (people * lPerPersonPerDay))
}

export type SupplyStatus = 'excellent' | 'good' | 'moderate' | 'low'

export function supplyStatus(days: number): SupplyStatus {
  if (days >= 365) return 'excellent'
  if (days >= 90) return 'good'
  if (days >= 30) return 'moderate'
  return 'low'
}

export interface TankRec {
  label: string
  days: number
  liters: number
}

const TANK_REC_LABELS = ['Minimum', 'Anbefalt', 'Robust']

export function tankRecommendations(
  people: number,
  lPerPersonPerDay: number,
  days: number[],
): TankRec[] {
  const dailyNeed = people * lPerPersonPerDay
  return days.map((d, i) => ({
    label: TANK_REC_LABELS[i] ?? `${d} dager`,
    days: d,
    liters: Math.ceil((dailyNeed * d) / 100) * 100,
  }))
}
