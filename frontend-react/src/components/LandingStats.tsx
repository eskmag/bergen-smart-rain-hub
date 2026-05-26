import type { LandingStatsProps } from './LandingHero'

function s(value: number, loading: boolean, decimals = 0): string {
  if (loading) return '—'
  return value.toLocaleString('nb-NO', { maximumFractionDigits: decimals })
}

export default function LandingStats({
  totalMm, longestDryDays, roofCollectionKL, buildingTypeCount, isLoading,
}: LandingStatsProps) {
  return (
    <div className="l-stats-strip">
      <div className="l-ss-item">
        <div className="l-ss-num">{s(totalMm, isLoading)} mm</div>
        <div className="l-ss-label">Nedbør siste år</div>
      </div>
      <div className="l-ss-item">
        <div className="l-ss-num">{s(longestDryDays, isLoading)} dager</div>
        <div className="l-ss-label">Lengste tørkeperiode</div>
      </div>
      <div className="l-ss-item">
        <div className="l-ss-num">{s(roofCollectionKL * 1000, isLoading)} L</div>
        <div className="l-ss-label">Fra ett hustak (150 m²)</div>
      </div>
      <div className="l-ss-item">
        <div className="l-ss-num">{isLoading ? '—' : buildingTypeCount} typer</div>
        <div className="l-ss-label">Bygningstyper støttet</div>
      </div>
    </div>
  )
}
