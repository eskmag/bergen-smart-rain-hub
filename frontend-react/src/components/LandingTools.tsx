import { Link } from 'react-router-dom'

export default function LandingTools() {
  return (
    <section className="l-tools" id="verktoy">
      <div className="l-tools-header">
        <h2 className="l-tools-title">To verktøy, ett formål</h2>
        <span className="l-tools-meta">Alle basert på ekte nedbørsdata fra MET</span>
      </div>
      <div className="l-tools-grid">
        <div className="l-tool-cell">
          <div className="l-tool-index">01 · Kalkulator</div>
          <h3 className="l-tool-title">Beredskapskalkulator</h3>
          <p className="l-tool-body">
            Velg bygningstype og antall personer. Se umiddelbart beredskapspotensialet basert
            på WHO-standarder og ekte nedbørsdata fra Bergen Florida.
          </p>
          <Link to="/beregn" className="l-tool-link">
            Åpne kalkulator
            <svg className="l-icon-sm" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </Link>
        </div>
        <div className="l-tool-cell">
          <div className="l-tool-index">02 · Simulator</div>
          <h3 className="l-tool-title">Beredskapssimulator</h3>
          <p className="l-tool-body">
            Simuler tanknivå dag for dag gjennom et helt år. Test ulike scenarier og finn
            kritiske tørkeperioder som kan true vannforsyningen.
          </p>
          <Link to="/beredskap" className="l-tool-link">
            Åpne simulator
            <svg className="l-icon-sm" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </Link>
        </div>
      </div>
    </section>
  )
}
