import { createContext, useContext, useState, useEffect, useMemo, type ReactNode } from 'react'
import { useMutation } from '@tanstack/react-query'
import { api } from '../api/client'
import type { BeredskapsResponse } from '../api/client'

interface BeredskapsState {
  buildingKey: string
  setBuildingKey: (v: string) => void
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
  setHeightM: (v: number) => void
  simResult: BeredskapsResponse | undefined
  isSimPending: boolean
  annualLiters: number
}

const BeredskapsContext = createContext<BeredskapsState | null>(null)

// eslint-disable-next-line react-refresh/only-export-components
export function useBeredskap(): BeredskapsState {
  const ctx = useContext(BeredskapsContext)
  if (!ctx) throw new Error('useBeredskap must be used within BeredskapsProvider')
  return ctx
}

interface BeredskapsProviderProps {
  children: ReactNode
  initialRoofArea?: number
  initialNumBuildings?: number
  initialPopulation?: number
  initialTankLiters?: number
  initialScale?: string
  initialHeightM?: number
}

export function BeredskapsProvider({
  children,
  initialRoofArea = 120,
  initialNumBuildings = 1,
  initialPopulation = 4,
  initialTankLiters = 5000,
  initialScale = 'household',
  initialHeightM = 6,
}: BeredskapsProviderProps) {
  const [buildingKey, setBuildingKey] = useState('enebolig')
  const [roofPerBuilding, setRoofPerBuilding] = useState(initialRoofArea)
  const [numBuildings, setNumBuildings] = useState(initialNumBuildings)
  const [population, setPopulation] = useState(initialPopulation)
  const [tankLiters, setTankLiters] = useState(initialTankLiters)
  const [efficiency, setEfficiency] = useState(85)
  const [usageLevel, setUsageLevel] = useState('survival_total')
  const [scenario, setScenario] = useState('historical')
  const [scale, setScale] = useState(initialScale)
  const [heightM, setHeightM] = useState(initialHeightM)

  const simMutation = useMutation({ mutationFn: api.simulateBeredskap })

  useEffect(() => {
    const buildings = Array.from({ length: numBuildings }, (_, i) => ({
      label: `Bygg ${i + 1}`,
      roof_area_m2: roofPerBuilding,
      height_m: heightM,
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
  }, [roofPerBuilding, numBuildings, population, tankLiters, efficiency, usageLevel, scenario, heightM])

  const simResult = simMutation.data

  const annualLiters = useMemo(
    () => (simResult?.summary['total_collected_liters'] ?? 0) as number,
    [simResult],
  )

  return (
    <BeredskapsContext.Provider value={{
      buildingKey, setBuildingKey,
      roofPerBuilding, setRoofPerBuilding,
      numBuildings, setNumBuildings,
      population, setPopulation,
      tankLiters, setTankLiters,
      efficiency, setEfficiency,
      usageLevel, setUsageLevel,
      scenario, setScenario,
      scale, setScale,
      heightM, setHeightM,
      simResult,
      isSimPending: simMutation.isPending,
      annualLiters,
    }}>
      {children}
    </BeredskapsContext.Provider>
  )
}
