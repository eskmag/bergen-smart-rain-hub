import { useState, useEffect, useRef } from 'react'
import '../../takkart.css'

interface AddressSearchProps {
  onFlyTo: (point: [number, number] | null) => void
}

interface GeonorgeAddress {
  adressetekst: string
  representasjonspunkt: { lat: number; lon: number }
}

// Geonorge's `sok` matches whole words, not prefixes: "Torgall" returns 0 hits
// while "Torgallmenningen" returns 18. Since we search on every keystroke, the
// dropdown would stay empty until the user typed a complete street name — so
// append a wildcard to the last token ("Torgall" -> "Torgall*", "Torgall 1" ->
// "Torgall* 1", leaving the house number intact).
//
// Note: Geonorge does not transliterate input, so "Nygardsgaten" still finds
// nothing for "Nygårdsgaten" — the user has to type æ/ø/å.
function wildcardQuery(raw: string): string {
  const tokens = raw.trim().split(/\s+/)
  if (tokens.length === 0) return raw.trim()
  const streetEnd = tokens.length > 1 && /^\d/.test(tokens[tokens.length - 1])
    ? tokens.length - 2
    : tokens.length - 1
  const street = tokens[streetEnd]
  if (street && !street.endsWith('*')) tokens[streetEnd] = `${street}*`
  return tokens.join(' ')
}

export default function AddressSearch({ onFlyTo }: AddressSearchProps) {
  const [query, setQuery] = useState('')
  const [suggestions, setSuggestions] = useState<GeonorgeAddress[]>([])
  const [searchFailed, setSearchFailed] = useState(false)
  const [open, setOpen] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(async () => {
      if (query.trim().length < 2) {
        setSuggestions([])
        setSearchFailed(false)
        setOpen(false)
        return
      }
      try {
        const sok = wildcardQuery(query)
        const url = `https://ws.geonorge.no/adresser/v1/sok?sok=${encodeURIComponent(sok)}&kommunenummer=4601&treffPerSide=6&asciiKompatibel=true`
        const res = await fetch(url)
        if (!res.ok) throw new Error(`Geonorge ${res.status}`)
        const data = await res.json() as { adresser: GeonorgeAddress[] }
        setSuggestions(data.adresser ?? [])
        setSearchFailed(false)
        setOpen(true)
      } catch {
        // Surface the failure — silently returning made a broken search look
        // identical to "no such address".
        setSuggestions([])
        setSearchFailed(true)
        setOpen(true)
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

  // Navigation only. Automatic footprint lookup used to live here, via
  // Overpass, and it could not be made to work: Overpass answers 406 to any
  // request carrying a deployed site's Referer, its per-IP rate limit is
  // unusable from a shared cloud egress, and it blocks a developer's own
  // address after modest use. Drawing the roof is the reliable path, so the
  // search does what it can do dependably — puts the right roof on screen.
  function selectAddress(addr: GeonorgeAddress) {
    setQuery(addr.adressetekst)
    setOpen(false)
    const { lat, lon } = addr.representasjonspunkt
    onFlyTo([lat, lon])
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
          placeholder="Søk adresse for å finne taket…"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onFocus={() => suggestions.length > 0 && setOpen(true)}
          autoComplete="off"
        />
      </div>
      {open && suggestions.length === 0 && (
        <div className="t-address-dropdown">
          <p className="t-address-empty">
            {searchFailed
              ? 'Adressesøket er utilgjengelig akkurat nå. Prøv igjen, eller mål taket manuelt.'
              : 'Ingen treff i Bergen. Husk æ/ø/å i gatenavnet.'}
          </p>
        </div>
      )}
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
    </div>
  )
}
