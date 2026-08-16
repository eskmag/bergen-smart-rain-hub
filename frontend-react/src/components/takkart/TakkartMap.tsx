import { useEffect } from 'react'
import { MapContainer, TileLayer, GeoJSON, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import '@geoman-io/leaflet-geoman-free'
import '@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css'
import type { Feature, Polygon } from 'geojson'

// Fix Vite + Leaflet default marker icon path resolution
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: new URL('leaflet/dist/images/marker-icon-2x.png', import.meta.url).href,
  iconUrl: new URL('leaflet/dist/images/marker-icon.png', import.meta.url).href,
  shadowUrl: new URL('leaflet/dist/images/marker-shadow.png', import.meta.url).href,
})

interface TakkartMapProps {
  polygon: Feature<Polygon> | null
  onPolygon: (feature: Feature<Polygon> | null) => void
  flyToPoint: [number, number] | null
  onFlyTo: (point: [number, number] | null) => void
  drawEnabled: boolean
}

function FlyToController({ flyToPoint, onFlyTo }: {
  flyToPoint: [number, number] | null
  onFlyTo: (point: [number, number] | null) => void
}) {
  const map = useMap()

  useEffect(() => {
    if (!flyToPoint) return
    map.flyTo(flyToPoint, 18, { duration: 1.2 })
    onFlyTo(null)
  }, [flyToPoint, map, onFlyTo])

  return null
}

// Ensure the map lays out correctly when it becomes visible (e.g. inside a
// modal that was display:none until opened).
function InvalidateOnMount() {
  const map = useMap()
  useEffect(() => {
    const t = setTimeout(() => map.invalidateSize(), 0)
    return () => clearTimeout(t)
  }, [map])
  return null
}

function GeomanControl({ onPolygon }: {
  onPolygon: (feature: Feature<Polygon> | null) => void
}) {
  const map = useMap()

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
      onPolygon(geojson)
      // Remove drawn layer from map — we render it via <GeoJSON> instead
      map.removeLayer(layer)
      map.pm.disableDraw()
    }

    map.on('pm:create', onCreate)
    return () => {
      map.off('pm:create', onCreate)
      map.pm.removeControls()
    }
  }, [map, onPolygon])

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

export default function TakkartMap({
  polygon, onPolygon, flyToPoint, onFlyTo, drawEnabled,
}: TakkartMapProps) {
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
      <InvalidateOnMount />
      <FlyToController flyToPoint={flyToPoint} onFlyTo={onFlyTo} />
      {drawEnabled && <GeomanControl onPolygon={onPolygon} />}
    </MapContainer>
  )
}
