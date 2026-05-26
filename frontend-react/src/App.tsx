import { Routes, Route, NavLink } from 'react-router-dom'
import Home from './pages/Home'
import BeredskapsLayout from './pages/BeredskapsLayout'
import Simulering from './pages/Simulering'
import Risiko from './pages/Risiko'
import Kostnader from './pages/Kostnader'
import './App.css'

function navClass({ isActive }: { isActive: boolean }) {
  return isActive ? 'nav-link active' : 'nav-link'
}

export default function App() {
  return (
    <div className="app-shell">
      <nav className="nav">
        <NavLink to="/" end className="nav-brand">
          🌧️ Bergen Rain Hub
        </NavLink>
        <NavLink to="/beredskap" end className={navClass}>Simulering</NavLink>
        <NavLink to="/beredskap/risiko" className={navClass}>Risiko</NavLink>
        <NavLink to="/beredskap/kostnader" className={navClass}>Kostnader</NavLink>
      </nav>
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/beredskap" element={<BeredskapsLayout />}>
            <Route index element={<Simulering />} />
            <Route path="risiko" element={<Risiko />} />
            <Route path="kostnader" element={<Kostnader />} />
          </Route>
        </Routes>
      </main>
    </div>
  )
}
