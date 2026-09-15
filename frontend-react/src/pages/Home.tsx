import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import type { Observation, ConfigResponse } from '../api/client'
import LandingNav from '../components/LandingNav'
import LandingHero from '../components/LandingHero'
import LandingNarrative from '../components/LandingNarrative'
import LandingCTA from '../components/LandingCTA'
import '../landing.css'

// Example roof used for the landing-page figure — a typical enebolig roof
const EXAMPLE_ROOF_M2 = 150

function roofCollectionLiters(observations: Observation[], config: ConfigResponse) {
  const totalMm = observations.reduce((s, o) => s + o.precipitation_mm, 0)
  // Rounded to whole thousands: it is a talking point, not a measurement
  const liters = totalMm * config.defaults.collection_efficiency * EXAMPLE_ROOF_M2
  return Math.round(liters / 1000) * 1000
}

export default function Home() {
  const { data: config } = useQuery({ queryKey: ['config'], queryFn: api.config })
  const { data: observations } = useQuery({
    queryKey: ['observations'],
    queryFn: () => api.observations(365),
    enabled: !!config,
  })

  const liters = useMemo(
    () => (observations && config ? roofCollectionLiters(observations, config) : null),
    [observations, config],
  )

  return (
    <div className="l-shell">
      <LandingNav />
      <LandingHero roofCollectionLiters={liters} roofM2={EXAMPLE_ROOF_M2} />
      <LandingNarrative />
      <LandingCTA />
    </div>
  )
}
