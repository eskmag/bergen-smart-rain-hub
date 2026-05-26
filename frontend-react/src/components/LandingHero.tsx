import { Link } from 'react-router-dom'

export interface LandingStatsProps {
  totalMm: number
  longestDryDays: number
  roofCollectionKL: number
  buildingTypeCount: number
  isLoading: boolean
}

function s(value: number, loading: boolean, decimals = 0): string {
  if (loading) return '—'
  return value.toLocaleString('nb-NO', { maximumFractionDigits: decimals })
}

export default function LandingHero({
  totalMm, longestDryDays, roofCollectionKL, buildingTypeCount, isLoading,
}: LandingStatsProps) {
  return (
    <section className="l-hero">
      <div>
        <p className="l-eyebrow">Regnvannsbasert beredskap · Bergen, Norge</p>
        <h1 className="l-hero-title">
          Bergen mottar<br />
          <strong>nok vann til alt</strong> —<br />
          men er ikke forberedt
        </h1>
        <p className="l-hero-sub">
          Vi beregner det reelle beredskapspotensialet i regnvannet over Bergen,
          basert på daglige målinger fra Meteorologisk Institutt.
        </p>
        <div className="l-hero-actions">
          <Link to="/beregn" className="l-btn-primary">
            <svg className="l-icon" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M9 7H6a2 2 0 00-2 2v9a2 2 0 002 2h9a2 2 0 002-2v-3M13 3h8m0 0v8m0-8L11 13" />
            </svg>
            Beregn ditt bygg
          </Link>
          <button
            className="l-btn-ghost"
            onClick={() => document.getElementById('bakgrunn')?.scrollIntoView({ behavior: 'smooth' })}
          >
            Les historien
            <svg className="l-icon-sm" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>
      </div>
      <div className="l-hero-right">
        <div className="l-hero-stat-main">
          <div className="l-hsm-num">{s(totalMm, isLoading)} mm</div>
          <div className="l-hsm-label">Nedbør i Bergen · siste 12 måneder</div>
        </div>
        <div className="l-hero-stat-grid">
          <div className="l-hsg-item">
            <div className="l-hsg-num">{s(longestDryDays, isLoading)} d</div>
            <div className="l-hsg-label">Lengste tørkeperiode</div>
          </div>
          <div className="l-hsg-item">
            <div className="l-hsg-num">{s(roofCollectionKL, isLoading)} kL</div>
            <div className="l-hsg-label">Fra ett hustak i år</div>
          </div>
          <div className="l-hsg-item">
            <div className="l-hsg-num">{isLoading ? '—' : buildingTypeCount}</div>
            <div className="l-hsg-label">Bygningstyper støttet</div>
          </div>
          <div className="l-hsg-item">
            <div className="l-hsg-num">13 L</div>
            <div className="l-hsg-label">WHO-min / dag / person</div>
          </div>
        </div>
      </div>
    </section>
  )
}
