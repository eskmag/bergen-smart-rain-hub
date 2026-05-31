import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Beregn from './pages/Beregn'
import { BeredskapsProvider } from './context/BeredskapsContext'
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
    </Routes>
  )
}
