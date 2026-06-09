import { useEffect } from 'react'
import { MapContainer, TileLayer, GeoJSON, useMap } from 'react-leaflet'
import L from 'leaflet'
import '@geoman-io/leaflet-geoman-free'
import type { Feature, Polygon } from 'geojson'
import { useTakkart } from '../../context/TakkartContext'

// Fix Vite + Leaflet default marker icon path resolution
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: new URL('leaflet/dist/images/marker-icon-2x.png', import.meta.url).href,
  iconUrl: new URL('leaflet/dist/images/marker-icon.png', import.meta.url).href,
  shadowUrl: new URL('leaflet/dist/images/marker-shadow.png', import.meta.url).href,
})

function FlyToController() {
  const map = useMap()
  const { flyToPoint, setFlyToPoint } = useTakkart()

  useEffect(() => {
    if (!flyToPoint) return
    map.flyTo(flyToPoint, 18, { duration: 1.2 })
    setFlyToPoint(null)
  }, [flyToPoint, map, setFlyToPoint])

  return null
}

function GeomanControl() {
  const map = useMap()
  const { setPolygon } = useTakkart()

  useEffect(() => {
    map.pm.addControls({
      position: 'topleft',
      drawPolygon: true,
      editMode: false,
      dragMode: false,
      cutPolygon: false,
      removalMode: true,
      drawMarker: false,
      drawCircle: false,
      drawCircleMarker: false,
      drawText: false,
      drawRectangle: false,
      drawPolyline: false,
    })

    function onCreate(e: { layer: L.Layer }) {
      const layer = e.layer as L.Polygon
      const geojson = layer.toGeoJSON() as Feature<Polygon>
      setPolygon(geojson)
      // Remove drawn layer from map — we render it via <GeoJSON> instead
      map.removeLayer(layer)
      map.pm.disableDraw()
    }

    map.on('pm:create', onCreate)
    return () => {
      map.off('pm:create', onCreate)
      map.pm.removeControls()
    }
  }, [map, setPolygon])

  return null
}

const KARTVERK_URL =
  'https://cache.kartverket.no/v1/wmts/1.0.0/topo/default/webmercator/{z}/{y}/{x}.png'
const OSM_URL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'

const POLYGON_STYLE = {
  color: '#1B6CA8',
  weight: 2,
  fillColor: '#EBF3FB',
  fillOpacity: 0.45,
}

export default function TakkartMap() {
  const { polygon, mode } = useTakkart()

  return (
    <MapContainer
      center={[60.3913, 5.3221]}
      zoom={13}
      style={{ flex: 1, minHeight: 400 }}
      zoomControl={true}
    >
      {/* OSM as base fallback (lower zIndex) */}
      <TileLayer
        url={OSM_URL}
        attribution="© OpenStreetMap"
        zIndex={1}
      />
      {/* Kartverket topographic tiles on top */}
      <TileLayer
        url={KARTVERK_URL}
        attribution="© Kartverket"
        zIndex={2}
      />
      {polygon && (
        <GeoJSON
          key={JSON.stringify(polygon.geometry.coordinates[0][0])}
          data={polygon}
          style={POLYGON_STYLE}
        />
      )}
      <FlyToController />
      {mode === 'manual' && <GeomanControl />}
    </MapContainer>
  )
}
