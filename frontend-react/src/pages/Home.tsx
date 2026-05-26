import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import type { Observation, ConfigResponse } from '../api/client'
import LandingNav from '../components/LandingNav'
import LandingHero from '../components/LandingHero'
import LandingStats from '../components/LandingStats'
import LandingNarrative from '../components/LandingNarrative'
import LandingTools from '../components/LandingTools'
import LandingData from '../components/LandingData'
import LandingCTA from '../components/LandingCTA'
import '../landing.css'

function computeStats(observations: Observation[], config: ConfigResponse | undefined) {
  const totalMm = Math.round(observations.reduce((s, o) => s + o.precipitation_mm, 0))

  let maxDry = 0, cur = 0
  for (const o of observations) {
    if (o.precipitation_mm < 0.1) { cur++; maxDry = Math.max(maxDry, cur) }
    else cur = 0
  }

  const roofCollectionKL = Math.round(totalMm * 0.85 * 150 / 1000)
  const buildingTypeCount = config?.building_presets.length ?? 0

  return { totalMm, longestDryDays: maxDry, roofCollectionKL, buildingTypeCount }
}

export default function Home() {
  const { data: config } = useQuery({ queryKey: ['config'], queryFn: api.config })
  const { data: observations, isLoading } = useQuery({
    queryKey: ['observations'],
    queryFn: () => api.observations(365),
    enabled: !!config,
  })

  const stats = useMemo(
    () => (observations ? computeStats(observations, config) : null),
    [observations, config],
  )

  const statsProps = {
    totalMm:           stats?.totalMm          ?? 0,
    longestDryDays:    stats?.longestDryDays    ?? 0,
    roofCollectionKL:  stats?.roofCollectionKL  ?? 0,
    buildingTypeCount: stats?.buildingTypeCount ?? 0,
    isLoading: isLoading || !stats,
  }

  return (
    <div className="l-shell">
      <LandingNav />
      <LandingHero {...statsProps} />
      <LandingStats {...statsProps} />
      <LandingNarrative />
      <LandingTools />
      <LandingData />
      <LandingCTA />
    </div>
  )
}
