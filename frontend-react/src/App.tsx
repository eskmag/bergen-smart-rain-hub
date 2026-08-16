import { Routes, Route, Navigate, Outlet, useSearchParams } from 'react-router-dom'
import Home from './pages/Home'
import Beregn from './pages/Beregn'
import Rapport from './pages/Rapport'
import Potensial from './pages/Potensial'
import { BeredskapsProvider } from './context/BeredskapsContext'
import './App.css'

// Shared BeredskapsProvider for /beregn and /rapport, so a "Generer
// rapport" navigation carries the calculator state over instead of
// resetting to defaults.
function BeregnLayout() {
  const [params] = useSearchParams()
  const areal = params.get('areal')
  const initialRoofArea = areal ? Math.round(parseFloat(areal)) : undefined
  return (
    <BeredskapsProvider initialRoofArea={initialRoofArea}>
      <Outlet />
    </BeredskapsProvider>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/potensial" element={<Potensial />} />
      <Route element={<BeregnLayout />}>
        <Route path="/beregn" element={<Beregn />} />
        <Route path="/rapport" element={<Rapport />} />
      </Route>
      {/* /takkart merged into the calculator (roof measurement is now a mode of /beregn) */}
      <Route path="/takkart" element={<Navigate to="/beregn" replace />} />
    </Routes>
  )
}
