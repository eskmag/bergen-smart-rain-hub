import { Link } from 'react-router-dom'

// Calculator-specific top nav: back-to-home link + title + decorative
// step pills. Pills are static visual indicators, not a wizard flow.
export default function BeregnNav() {
  return (
    <nav className="k-nav">
      <div className="k-nav-left">
        <Link className="k-nav-back" to="/">
          <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path d="M19 12H5M12 5l-7 7 7 7" />
          </svg>
          Hjem
        </Link>
        <div className="k-nav-divider" />
        <span className="k-nav-title">Beredskapskalkulator</span>
      </div>
      <div className="k-nav-steps">
        <span className="k-step-pill done">01 Bygningstype</span>
        <span className="k-step-sep">·</span>
        <span className="k-step-pill active">02 Personer</span>
        <span className="k-step-sep">·</span>
        <span className="k-step-pill">03 Tank</span>
      </div>
    </nav>
  )
}
