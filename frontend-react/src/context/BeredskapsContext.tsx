import { createContext, useContext, useState, useEffect, useMemo, type ReactNode } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import area from '@turf/area'
import type { Feature, Polygon } from 'geojson'
import { api } from '../api/client'
import type { BeredskapsResponse, ScaleSchema } from '../api/client'

export type RoofSource = 'preset' | 'manual' | 'map'

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
  roofMaterial: string
  setRoofMaterial: (v: string) => void
  station: string
  setStation: (v: string) => void
  heightM: number
  setHeightM: (v: number) => void
  // Roof-area source of truth: three input methods write into roofPerBuilding.
  roofSource: RoofSource
  setRoofSource: (v: RoofSource) => void
  polygon: Feature<Polygon> | null
  setPolygon: (v: Feature<Polygon> | null) => void
  // Scale is derived from population (used by costs / EnergyCard / treatment).
  scale: string
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

// Derive scale from population: first scale (household → neighbourhood →
// infrastructure) whose typical_population upper bound covers the count.
// Bounds come from /api/config (backend/scales.py) — no hardcoded mirror.
function deriveScale(population: number, scales: ScaleSchema[] | undefined): string {
  if (!scales || scales.length === 0) {
    // Fallback if config not yet loaded (matches backend typical_population).
    if (population <= 60) return 'household'
    if (population <= 500) return 'neighbourhood'
    return 'infrastructure'
  }
  const order = ['household', 'neighbourhood', 'infrastructure']
  const ordered = order
    .map(key => scales.find(s => s.key === key))
    .filter((s): s is ScaleSchema => s !== undefined)
  for (const s of ordered) {
    if (population <= s.typical_population[1]) return s.key
  }
  return ordered[ordered.length - 1]?.key ?? 'infrastructure'
}

interface BeredskapsProviderProps {
  children: ReactNode
  initialRoofArea?: number
  initialNumBuildings?: number
  initialPopulation?: number
  initialTankLiters?: number
  initialHeightM?: number
}

export function BeredskapsProvider({
  children,
  initialRoofArea = 120,
  initialNumBuildings = 1,
  initialPopulation = 4,
  initialTankLiters = 5000,
  // matches the 'enebolig' preset (BUILDING_PRESETS in backend/analysis.py);
  // replaced as soon as the user picks a building type
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
  const [roofMaterial, setRoofMaterial] = useState('takstein')
  const [station, setStation] = useState('SN50540')
  const [heightM, setHeightM] = useState(initialHeightM)
  const [roofSource, setRoofSource] = useState<RoofSource>('preset')
  const [polygonState, setPolygonState] = useState<Feature<Polygon> | null>(null)

  const { data: config } = useQuery({ queryKey: ['config'], queryFn: api.config })
  const scale = useMemo(
    () => deriveScale(population, config?.scales),
    [population, config],
  )

  // Setting a polygon (from the map) makes it the roof-area source of truth.
  function setPolygon(feature: Feature<Polygon> | null) {
    setPolygonState(feature)
    if (feature) {
      setRoofPerBuilding(Math.round(area(feature)))
      setRoofSource('map')
    }
  }

  const simMutation = useMutation({ mutationFn: api.simulateBeredskap })

  useEffect(() => {
    const buildings = Array.from({ length: numBuildings }, (_, i) => ({
      name: `Bygg ${i + 1}`,
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
      station,
    })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [roofPerBuilding, numBuildings, population, tankLiters, efficiency, usageLevel, scenario, heightM, station])

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
      roofMaterial, setRoofMaterial,
      station, setStation,
      heightM, setHeightM,
      roofSource, setRoofSource,
      polygon: polygonState, setPolygon,
      scale,
      simResult,
      isSimPending: simMutation.isPending,
      annualLiters,
    }}>
      {children}
    </BeredskapsContext.Provider>
  )
}
