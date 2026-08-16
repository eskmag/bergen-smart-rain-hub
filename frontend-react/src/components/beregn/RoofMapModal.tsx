import { useState } from 'react'
import area from '@turf/area'
import type { Feature, Polygon } from 'geojson'
import TakkartMap from '../takkart/TakkartMap'
import AddressSearch from '../takkart/AddressSearch'

function fmt(n: number) {
  return Math.round(n).toLocaleString('nb-NO')
}

interface RoofMapModalProps {
  initialPolygon: Feature<Polygon> | null
  onUse: (feature: Feature<Polygon>) => void
  onClose: () => void
}

// Full-width overlay for measuring a roof: search a Bergen address to pull the
// building footprint, or draw a polygon manually. Commits the chosen polygon
// back to the calculator via onUse.
export default function RoofMapModal({ initialPolygon, onUse, onClose }: RoofMapModalProps) {
  const [polygon, setPolygon] = useState<Feature<Polygon> | null>(initialPolygon)
  const [flyToPoint, setFlyToPoint] = useState<[number, number] | null>(null)

  const roofAreaM2 = polygon !== null ? area(polygon) : null

  return (
    <div className="k-modal-backdrop" onMouseDown={onClose}>
      <div className="k-modal" onMouseDown={e => e.stopPropagation()}>
        <div className="k-modal-header">
          <div>
            <div className="k-modal-eyebrow">Mål taket</div>
            <div className="k-modal-title">Søk adresse eller tegn takflaten</div>
          </div>
          <button className="k-modal-close" type="button" onClick={onClose} aria-label="Lukk">
            ×
          </button>
        </div>

        <div className="k-modal-search">
          <AddressSearch onPolygon={setPolygon} onFlyTo={setFlyToPoint} />
        </div>

        <div className="k-modal-map">
          <TakkartMap
            polygon={polygon}
            onPolygon={setPolygon}
            flyToPoint={flyToPoint}
            onFlyTo={setFlyToPoint}
            drawEnabled
          />
        </div>

        <div className="k-modal-footer">
          <div className="k-modal-area">
            {roofAreaM2 !== null
              ? <>Målt takflate: <strong>{fmt(roofAreaM2)} m²</strong></>
              : 'Søk opp en adresse eller tegn et polygon på kartet'}
          </div>
          <div className="k-modal-actions">
            <button className="k-modal-cancel" type="button" onClick={onClose}>
              Avbryt
            </button>
            <button
              className="k-modal-use"
              type="button"
              disabled={polygon === null}
              onClick={() => polygon && onUse(polygon)}
            >
              Bruk dette taket
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
