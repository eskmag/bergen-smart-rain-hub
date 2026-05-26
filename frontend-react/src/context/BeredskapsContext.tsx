import { createContext, useContext, useState, useEffect, useMemo, type ReactNode } from 'react'
import { useMutation } from '@tanstack/react-query'
import { api } from '../api/client'
import type { BeredskapsResponse, RiskAssessResponse } from '../api/client'

interface BeredskapsState {
  roofPerBuilding: number
  setRoofPerBuilding: (v: number) => void
  numBuildings: number
  setNumBuildings: (v: number) => void
  population: number
  setPopulation: (v: number) => void
  tankLiters: number
  setTankLiters: (v: number) => void
  efficiency: number
  setEfficiency: (v: number) => void
  usageLevel: string
  setUsageLevel: (v: string) => void
  scenario: string
  setScenario: (v: string) => void
  scale: string
  setScale: (v: string) => void
  heightM: number
  simResult: BeredskapsResponse | undefined
  isSimPending: boolean
  annualLiters: number
  riskResult: RiskAssessResponse | undefined
  isRiskPending: boolean
}

const BeredskapsContext = createContext<BeredskapsState | null>(null)

export function useBeredskap(): BeredskapsState {
  const ctx = useContext(BeredskapsContext)
  if (!ctx) throw new Error('useBeredskap must be used within BeredskapsProvider')
  return ctx
}

interface BeredskapsProviderProps {
  children: ReactNode
  initialRoofArea: number
  initialNumBuildings: number
  initialPopulation: number
  initialTankLiters: number
  initialScale: string
  initialHeightM: number
}

export function BeredskapsProvider({
  children,
  initialRoofArea,
  initialNumBuildings,
  initialPopulation,
  initialTankLiters,
  initialScale,
  initialHeightM,
}: BeredskapsProviderProps) {
  const [roofPerBuilding, setRoofPerBuilding] = useState(initialRoofArea)
  const [numBuildings, setNumBuildings] = useState(initialNumBuildings)
  const [population, setPopulation] = useState(initialPopulation)
  const [tankLiters, setTankLiters] = useState(initialTankLiters)
  const [efficiency, setEfficiency] = useState(85)
  const [usageLevel, setUsageLevel] = useState('survival_total')
  const [scenario, setScenario] = useState('historical')
  const [scale, setScale] = useState(initialScale)

  const simMutation = useMutation({ mutationFn: api.simulateBeredskap })
  const riskMutation = useMutation({ mutationFn: api.assessRisk })

  useEffect(() => {
    const buildings = Array.from({ length: numBuildings }, (_, i) => ({
      label: `Bygg ${i + 1}`,
      roof_area_m2: roofPerBuilding,
      height_m: initialHeightM,
    }))
    simMutation.mutate({
      buildings,
      tank_liters: tankLiters,
      population,
      efficiency: efficiency / 100,
      usage_level: usageLevel,
      climate_scenario: scenario,
    })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [roofPerBuilding, numBuildings, population, tankLiters, efficiency, usageLevel, scenario])

  const simResult = simMutation.data

  useEffect(() => {
    if (!simResult) return
    riskMutation.mutate({
      tank_liters: tankLiters,
      population,
      roof_area_m2: roofPerBuilding * numBuildings,
      scale,
      days_tank_empty: simResult.summary['days_tank_empty'] ?? 0,
      longest_dry_spell: simResult.summary['longest_dry_spell_days'] ?? 0,
    })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [simResult, scale])

  const annualLiters = useMemo(
    () => (simResult?.summary['total_collected_liters'] ?? 0) as number,
    [simResult],
  )

  return (
    <BeredskapsContext.Provider value={{
      roofPerBuilding, setRoofPerBuilding,
      numBuildings, setNumBuildings,
      population, setPopulation,
      tankLiters, setTankLiters,
      efficiency, setEfficiency,
      usageLevel, setUsageLevel,
      scenario, setScenario,
      scale, setScale,
      heightM: initialHeightM,
      simResult,
      isSimPending: simMutation.isPending,
      annualLiters,
      riskResult: riskMutation.data,
      isRiskPending: riskMutation.isPending,
    }}>
      {children}
    </BeredskapsContext.Provider>
  )
}
