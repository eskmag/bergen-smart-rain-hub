import { Routes, Route, useSearchParams } from 'react-router-dom'
import Home from './pages/Home'
import Beregn from './pages/Beregn'
import Takkart from './pages/Takkart'
import { BeredskapsProvider } from './context/BeredskapsContext'
import { TakkartProvider } from './context/TakkartContext'
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
      <Route
        path="/beregn"
        element={<BeregnRoute />}
      />
      <Route
        path="/takkart"
        element={
          <TakkartProvider>
            <Takkart />
          </TakkartProvider>
        }
      />
    </Routes>
  )
}
