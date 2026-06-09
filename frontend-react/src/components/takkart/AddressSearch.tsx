import { useState, useEffect, useRef } from 'react'
import { useTakkart } from '../../context/TakkartContext'
import type { Feature, Polygon } from 'geojson'

interface GeonorgeAddress {
  adressetekst: string
  representasjonspunkt: { lat: number; lon: number }
}

interface OverpassElement {
  type: 'way' | 'relation'
  geometry?: { lat: number; lon: number }[]
  members?: { type: string; geometry?: { lat: number; lon: number }[] }[]
}

function pointInPolygon(pt: [number, number], ring: [number, number][]): boolean {
  let inside = false
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const xi = ring[i][0], yi = ring[i][1]
    const xj = ring[j][0], yj = ring[j][1]
    if ((yi > pt[1]) !== (yj > pt[1]) && pt[0] < ((xj - xi) * (pt[1] - yi)) / (yj - yi) + xi) {
      inside = !inside
    }
  }
  return inside
}

function ringToCoords(geom: { lat: number; lon: number }[]): [number, number][] {
  return geom.map(p => [p.lon, p.lat])
}

function buildPolygonFeature(coords: [number, number][]): Feature<Polygon> {
  const closed = coords[0][0] === coords[coords.length - 1][0] &&
    coords[0][1] === coords[coords.length - 1][1]
      ? coords
      : [...coords, coords[0]]
  return { type: 'Feature', properties: {}, geometry: { type: 'Polygon', coordinates: [closed] } }
}

async function fetchFootprint(
  lat: number,
  lon: number,
): Promise<Feature<Polygon> | null> {
  const query = `[out:json];(way(around:35,${lat},${lon})["building"];relation(around:35,${lat},${lon})["building"];);out geom;`
  const res = await fetch('https://overpass-api.de/api/interpreter', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'User-Agent': 'BergenSmartRainHub/1.0',
    },
    body: `data=${encodeURIComponent(query)}`,
  })
  if (!res.ok) throw new Error(`Overpass ${res.status}`)
  const data = await res.json() as { elements: OverpassElement[] }

  const pt: [number, number] = [lon, lat]
  let best: Feature<Polygon> | null = null

  for (const el of data.elements) {
    if (el.type === 'way' && el.geometry && el.geometry.length >= 3) {
      const coords = ringToCoords(el.geometry)
      const feature = buildPolygonFeature(coords)
      if (pointInPolygon(pt, coords)) return feature
      best = best ?? feature
    }
    if (el.type === 'relation' && el.members) {
      const outer = el.members.find(m => m.type === 'way' && m.geometry)
      if (outer?.geometry && outer.geometry.length >= 3) {
        const coords = ringToCoords(outer.geometry)
        const feature = buildPolygonFeature(coords)
        if (pointInPolygon(pt, coords)) return feature
        best = best ?? feature
      }
    }
  }
  return best
}

export default function AddressSearch() {
  const { setPolygon, setFlyToPoint } = useTakkart()
  const [query, setQuery] = useState('')
  const [suggestions, setSuggestions] = useState<GeonorgeAddress[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [open, setOpen] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(async () => {
      if (query.length < 2) {
        setSuggestions([])
        setOpen(false)
        return
      }
      try {
        const url = `https://ws.geonorge.no/adresser/v1/sok?sok=${encodeURIComponent(query)}&kommunenummer=4601&treffPerSide=6&asciiKompatibel=true`
        const res = await fetch(url)
        if (!res.ok) return
        const data = await res.json() as { adresser: GeonorgeAddress[] }
        setSuggestions(data.adresser ?? [])
        setOpen(true)
      } catch {
        // ignore transient errors
      }
    }, 300)
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current) }
  }, [query])

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [])

  async function selectAddress(addr: GeonorgeAddress) {
    setQuery(addr.adressetekst)
    setOpen(false)
    setError(null)
    const { lat, lon } = addr.representasjonspunkt
    setFlyToPoint([lat, lon])
    setLoading(true)
    try {
      const footprint = await fetchFootprint(lat, lon)
      if (footprint) {
        setPolygon(footprint)
      } else {
        setError('Fant ingen bygningsfotavtrykk i nærheten. Prøv å måle manuelt.')
      }
    } catch {
      setError('Kunne ikke hente bygningsdata. Prøv igjen eller mål manuelt.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="t-address-wrap" ref={containerRef}>
      <div className="t-address-field">
        <svg className="t-address-icon" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
          <circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" />
        </svg>
        <input
          className="t-address-input"
          type="text"
          placeholder="Søk adresse i Bergen…"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onFocus={() => suggestions.length > 0 && setOpen(true)}
          autoComplete="off"
        />
        {loading && <div className="t-address-spinner" />}
      </div>
      {open && suggestions.length > 0 && (
        <ul className="t-address-dropdown">
          {suggestions.map((s, i) => (
            <li key={i}>
              <button
                className="t-address-option"
                type="button"
                onMouseDown={() => selectAddress(s)}
              >
                <svg width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" />
                </svg>
                {s.adressetekst}
              </button>
            </li>
          ))}
        </ul>
      )}
      {error && <p className="t-address-error">{error}</p>}
      {/* TODO (produksjon): Bytt Overpass mot Kartverket FKB-Bygning for offisielle takflater */}
    </div>
  )
}
