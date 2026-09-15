import { Link } from 'react-router-dom'
import Kjelder from './shared/Kjelder'

export default function LandingCTA() {
  return (
    <>
      <section className="l-cta-section">
        <div className="l-cta-left">
          <h2 className="l-cta-title">Hvor lenge holder vannet i ditt bygg?</h2>
          <Link to="/potensial" className="l-cta-secondary">
            Eller se potensialet for hele Bergen
          </Link>
        </div>
        <div className="l-cta-right">
          <Link to="/beregn" className="l-cta-btn">
            <svg className="l-icon" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M9 7H6a2 2 0 00-2 2v9a2 2 0 002 2h9a2 2 0 002-2v-3M13 3h8m0 0v8m0-8L11 13" />
            </svg>
            Beregn ditt bygg
          </Link>
        </div>
      </section>
      <footer className="l-footer">
        <span className="l-footer-left">
          © 2026 Bergen Smart Rain Hub · Nedbørsdata: Meteorologisk institutt
        </span>
        <ul className="l-footer-links">
          <li><a href="#bakgrunn">Om prosjektet</a></li>
          <li><Link to="/potensial">Potensial</Link></li>
        </ul>
      </footer>
      <div className="l-footer-kjelder">
        <Kjelder />
      </div>
    </>
  )
}
