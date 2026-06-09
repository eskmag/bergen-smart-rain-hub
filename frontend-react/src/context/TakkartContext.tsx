import { createContext, useContext, useState, useEffect, useRef, type ReactNode } from 'react'
import { useMutation } from '@tanstack/react-query'
import area from '@turf/area'
import { api } from '../api/client'
import type { BeredskapsResponse } from '../api/client'
import type { Feature, Polygon } from 'geojson'

interface TakkartState {
  mode: 'address' | 'manual'
  setMode: (v: 'address' | 'manual') => void
  polygon: Feature<Polygon> | null
  setPolygon: (v: Feature<Polygon> | null) => void
  roofAreaM2: number | null
  numPeople: number
  setNumPeople: (v: number) => void
  flyToPoint: [number, number] | null
  setFlyToPoint: (v: [number, number] | null) => void
  simResult: BeredskapsResponse | null
  isSimPending: boolean
}

const TakkartContext = createContext<TakkartState | null>(null)

// eslint-disable-next-line react-refresh/only-export-components
export function useTakkart(): TakkartState {
  const ctx = useContext(TakkartContext)
  if (!ctx) throw new Error('useTakkart must be used within TakkartProvider')
  return ctx
}

interface TakkartProviderProps {
  children: ReactNode
}

export function TakkartProvider({ children }: TakkartProviderProps) {
  const [mode, setMode] = useState<'address' | 'manual'>('address')
  const [polygon, setPolygon] = useState<Feature<Polygon> | null>(null)
  const [numPeople, setNumPeople] = useState(4)
  const [flyToPoint, setFlyToPoint] = useState<[number, number] | null>(null)

  const roofAreaM2 = polygon !== null ? area(polygon) : null

  const simMutation = useMutation({ mutationFn: api.simulateBeredskap })
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (roofAreaM2 === null || numPeople < 1) return

    if (debounceRef.current !== null) {
      clearTimeout(debounceRef.current)
    }

    debounceRef.current = setTimeout(() => {
      simMutation.mutate({
        buildings: [{ label: 'Takkart', roof_area_m2: roofAreaM2, height_m: 7 }],
        tank_liters: Math.ceil((numPeople * 13 * 30) / 100) * 100,
        population: numPeople,
        efficiency: 0.85,
        usage_level: 'survival_total',
        climate_scenario: 'historical',
      })
    }, 500)

    return () => {
      if (debounceRef.current !== null) {
        clearTimeout(debounceRef.current)
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [roofAreaM2, numPeople])

  return (
    <TakkartContext.Provider value={{
      mode, setMode,
      polygon, setPolygon,
      roofAreaM2,
      numPeople, setNumPeople,
      flyToPoint, setFlyToPoint,
      simResult: simMutation.data ?? null,
      isSimPending: simMutation.isPending,
    }}>
      {children}
    </TakkartContext.Provider>
  )
}
