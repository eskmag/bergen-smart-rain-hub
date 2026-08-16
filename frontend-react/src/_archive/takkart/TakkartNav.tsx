import { Link } from 'react-router-dom'
import { useTakkart } from '../../context/TakkartContext'

export default function TakkartNav() {
  const { mode, setMode } = useTakkart()

  return (
    <nav className="t-nav">
      <div className="t-nav-left">
        <Link className="t-nav-back" to="/">
          <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path d="M19 12H5M12 5l-7 7 7 7" />
          </svg>
          Hjem
        </Link>
        <div className="t-nav-divider" />
        <span className="t-nav-title">Takkart · Mål takflate</span>
      </div>
      <div className="t-mode-toggle">
        <button
          className={`t-mode-btn${mode === 'address' ? ' active' : ''}`}
          onClick={() => setMode('address')}
          type="button"
        >
          <svg width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
            <circle cx="12" cy="10" r="3" />
          </svg>
          Søk adresse
        </button>
        <button
          className={`t-mode-btn${mode === 'manual' ? ' active' : ''}`}
          onClick={() => setMode('manual')}
          type="button"
        >
          <svg width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <polygon points="3 11 22 2 13 21 11 13 3 11" />
          </svg>
          Mål manuelt
        </button>
      </div>
    </nav>
  )
}
