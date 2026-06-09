export const ANNUAL_RAINFALL_MM = 2250
export const DEFAULT_EFFICIENCY = 0.85
export const WHO_L_PER_PERSON_PER_DAY = 13

// V (L) = A (m²) × R (mm) × C; mm/1000 → m³, ×1000 → L cancel out
export function annualCollectionLiters(roofM2: number, efficiency = DEFAULT_EFFICIENCY): number {
  return roofM2 * ANNUAL_RAINFALL_MM * efficiency
}

// Days the annual harvest can supply: annualL / (people × 13 L/day)
export function emergencyDays(annualL: number, people: number): number {
  return Math.floor(annualL / (people * WHO_L_PER_PERSON_PER_DAY))
}

export type SupplyStatus = 'excellent' | 'good' | 'moderate' | 'low'

export function supplyStatus(days: number): SupplyStatus {
  if (days >= 365) return 'excellent'
  if (days >= 90) return 'good'
  if (days >= 30) return 'moderate'
  return 'low'
}

export interface TankRec {
  label: 'Minimum' | 'Anbefalt' | 'Robust'
  days: 7 | 30 | 60
  liters: number
}

export function tankRecommendations(people: number): TankRec[] {
  const dailyNeed = people * WHO_L_PER_PERSON_PER_DAY

  return [
    {
      label: 'Minimum',
      days: 7,
      liters: Math.ceil((dailyNeed * 7) / 100) * 100,
    },
    {
      label: 'Anbefalt',
      days: 30,
      liters: Math.ceil((dailyNeed * 30) / 100) * 100,
    },
    {
      label: 'Robust',
      days: 60,
      liters: Math.ceil((dailyNeed * 60) / 100) * 100,
    },
  ]
}
