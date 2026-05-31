import { Routes, Route, NavLink, Outlet } from 'react-router-dom'
import Home from './pages/Home'
import Beregn from './pages/Beregn'
import BeredskapsLayout from './pages/BeredskapsLayout'
import Simulering from './pages/Simulering'
import Risiko from './pages/Risiko'
import Kostnader from './pages/Kostnader'
import { BeredskapsProvider } from './context/BeredskapsContext'
import './App.css'

function navClass({ isActive }: { isActive: boolean }) {
  return isActive ? 'nav-link active' : 'nav-link'
}

function BeredskapsRoot() {
  return (
    <BeredskapsProvider>
      <Outlet />
    </BeredskapsProvider>
  )
}

function AppShell() {
  return (
    <div className="app-shell">
      <nav className="nav">
        <NavLink to="/" end className="nav-brand">
          <div className="nav-logomark">
            <svg width="14" height="14" fill="none" viewBox="0 0 24 24">
              <path d="M12 2C8 8 5 12 5 16a7 7 0 0014 0c0-4-3-8-7-14z" fill="currentColor" />
            </svg>
          </div>
          Bergen Smart Rain Hub
        </NavLink>
        <NavLink to="/beregn" className={navClass}>Beregn</NavLink>
        <NavLink to="/beredskap" className={navClass}>Beredskap</NavLink>
      </nav>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route element={<BeredskapsRoot />}>
        <Route path="/beregn" element={<Beregn />} />
        <Route element={<AppShell />}>
          <Route path="/beredskap" element={<BeredskapsLayout />}>
            <Route index element={<Simulering />} />
            <Route path="risiko" element={<Risiko />} />
            <Route path="kostnader" element={<Kostnader />} />
          </Route>
        </Route>
      </Route>
    </Routes>
  )
}
