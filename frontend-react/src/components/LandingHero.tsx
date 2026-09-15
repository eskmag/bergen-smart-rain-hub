import { Link } from 'react-router-dom'

interface LandingHeroProps {
  /** Litres a typical roof collected over the last 12 months; null while loading. */
  roofCollectionLiters: number | null
  roofM2: number
}

export default function LandingHero({ roofCollectionLiters, roofM2 }: LandingHeroProps) {
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
          Finn ut hvor lenge regnvann fra ditt eget tak kan gi deg og dine
          trygt vann hvis vannforsyningen svikter.
        </p>
        <div className="l-hero-actions">
          <Link to="/beregn" className="l-btn-primary">
            <svg className="l-icon" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M9 7H6a2 2 0 00-2 2v9a2 2 0 002 2h9a2 2 0 002-2v-3M13 3h8m0 0v8m0-8L11 13" />
            </svg>
            Beregn ditt bygg
          </Link>
        </div>
      </div>
      <div className="l-hero-right">
        <div className="l-hero-stat-main">
          <div className="l-hsm-num">
            {roofCollectionLiters === null
              ? '—'
              : `${roofCollectionLiters.toLocaleString('nb-NO')} liter`}
          </div>
          <p className="l-hero-figure-text">
            så mye regnvann kunne et vanlig hustak på {roofM2} m² i Bergen
            samlet det siste året.
          </p>
        </div>
      </div>
    </section>
  )
}
