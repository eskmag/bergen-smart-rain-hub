import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Beregn from './pages/Beregn'
import Takkart from './pages/Takkart'
import { BeredskapsProvider } from './context/BeredskapsContext'
import { TakkartProvider } from './context/TakkartContext'
import './App.css'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route
        path="/beregn"
        element={
          <BeredskapsProvider>
            <Beregn />
          </BeredskapsProvider>
        }
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
