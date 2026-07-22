import { Routes, Route, Navigate, useSearchParams } from 'react-router-dom'
import Home from './pages/Home'
import Beregn from './pages/Beregn'
import Potensial from './pages/Potensial'
import { BeredskapsProvider } from './context/BeredskapsContext'
import './App.css'

function BeregnRoute() {
  const [params] = useSearchParams()
  const areal = params.get('areal')
  const initialRoofArea = areal ? Math.round(parseFloat(areal)) : undefined
  return (
    <BeredskapsProvider initialRoofArea={initialRoofArea}>
      <Beregn />
    </BeredskapsProvider>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/potensial" element={<Potensial />} />
      <Route path="/beregn" element={<BeregnRoute />} />
      {/* /takkart merged into the calculator (roof measurement is now a mode of /beregn) */}
      <Route path="/takkart" element={<Navigate to="/beregn" replace />} />
    </Routes>
  )
}
