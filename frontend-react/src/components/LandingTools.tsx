import { Link } from 'react-router-dom'

export default function LandingTools() {
  return (
    <section className="l-tools" id="verktoy">
      <div className="l-tools-header">
        <h2 className="l-tools-title">Beredskapskalkulatoren</h2>
        <span className="l-tools-meta">Basert på ekte nedbørsdata fra MET</span>
      </div>
      <div className="l-tools-grid">
        <div className="l-tool-cell">
          <div className="l-tool-index">01 · Kalkulator</div>
          <h3 className="l-tool-title">Beregn ditt bygg</h3>
          <p className="l-tool-body">
            Velg bygningstype og antall personer. Se umiddelbart hvor mange dager regnvann kan
            dekke vannbehovet, tanknivå dag for dag gjennom året, og hvilke tørkeperioder som
            kan true forsyningen — alt basert på WHO-standarder og ekte nedbørsdata fra Bergen Florida.
          </p>
          <Link to="/beregn" className="l-tool-link">
            Åpne kalkulator
            <svg className="l-icon-sm" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </Link>
        </div>
      </div>
    </section>
  )
}
