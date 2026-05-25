import { Routes, Route, NavLink } from 'react-router-dom'
import Home from './pages/Home'
import Vannberedskap from './pages/Vannberedskap'
import './App.css'

export default function App() {
  return (
    <div className="app-shell">
      <nav className="nav">
        <NavLink to="/" end className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
          Hjem
        </NavLink>
        <NavLink to="/beredskap" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
          Vannberedskap
        </NavLink>
      </nav>
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/beredskap" element={<Vannberedskap />} />
        </Routes>
      </main>
    </div>
  )
}
