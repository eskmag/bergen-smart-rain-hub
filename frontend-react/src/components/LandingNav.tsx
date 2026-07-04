import { Link } from 'react-router-dom'

export default function LandingNav() {
  return (
    <nav className="l-nav">
      <Link to="/" className="l-nav-logo">
        <div className="l-nav-logomark">
          <svg width="16" height="16" fill="none" viewBox="0 0 24 24">
            <path d="M12 2C8 8 5 12 5 16a7 7 0 0014 0c0-4-3-8-7-14z" fill="white" />
          </svg>
        </div>
        <span className="l-nav-logotype">Bergen Smart Rain Hub</span>
      </Link>
      <ul className="l-nav-links">
        {/* /#anker works from every route (plain href forces the navigation) */}
        <li><a href="/#bakgrunn">Om prosjektet</a></li>
        <li><a href="/#verktoy">Verktøy</a></li>
        <li><a href="/#data">Data</a></li>
        <li><Link to="/potensial">Potensial</Link></li>
      </ul>
      <Link to="/beregn" className="l-nav-cta">Beregn ditt bygg</Link>
    </nav>
  )
}
