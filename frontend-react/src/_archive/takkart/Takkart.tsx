import 'leaflet/dist/leaflet.css'
import '@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css'
import '../takkart.css'
import TakkartNav from '../components/takkart/TakkartNav'
import TakkartMap from '../components/takkart/TakkartMap'
import TakkartResultPanel from '../components/takkart/TakkartResultPanel'
import AddressSearch from '../components/takkart/AddressSearch'
import { useTakkart } from '../context/TakkartContext'

function TakkartLayout() {
  const { mode } = useTakkart()

  return (
    <div className="t-shell">
      <TakkartNav />
      <div className="t-layout">
        <div className="t-map-panel">
          {mode === 'address' && <AddressSearch />}
          <TakkartMap />
        </div>
        <TakkartResultPanel />
      </div>
    </div>
  )
}

export default function Takkart() {
  return <TakkartLayout />
}
