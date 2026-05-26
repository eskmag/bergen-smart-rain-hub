import { Link } from 'react-router-dom'

export default function LandingCTA() {
  return (
    <>
      <section className="l-cta-section">
        <div className="l-cta-left">
          <p className="l-cta-eyebrow">Kom i gang</p>
          <h2 className="l-cta-title">Klar til å beregne potensialet for ditt bygg?</h2>
          <p className="l-cta-sub">Under ett minutt · ingen registrering · gratis</p>
        </div>
        <div className="l-cta-right">
          <Link to="/beregn" className="l-cta-btn">
            <svg className="l-icon" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M9 7H6a2 2 0 00-2 2v9a2 2 0 002 2h9a2 2 0 002-2v-3M13 3h8m0 0v8m0-8L11 13" />
            </svg>
            Start beregning
          </Link>
          <p className="l-cta-note">Ekte nedbørsdata fra MET · WHO-standarder</p>
        </div>
      </section>
      <footer className="l-footer">
        <span className="l-footer-left">
          © 2026 Bergen Smart Rain Hub · Data: Meteorologisk Institutt, SN50540 Bergen Florida
        </span>
        <ul className="l-footer-links">
          <li><a href="#bakgrunn">Om prosjektet</a></li>
          <li><a href="#data">Datakilde</a></li>
        </ul>
      </footer>
    </>
  )
}
