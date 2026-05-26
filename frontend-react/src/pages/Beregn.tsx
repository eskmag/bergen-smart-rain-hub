import { useState, useMemo, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { api } from '../api/client'

function fmt(n: number, decimals = 0) {
  return n.toLocaleString('nb-NO', { maximumFractionDigits: decimals })
}

const BUILDING_OPTIONS = [
  { key: 'enebolig',        scale: 'household',     icon: '🏠', label: 'Enebolig',        sublabel: 'Frittstående hus' },
  { key: 'rekkehus',        scale: 'household',     icon: '🏘️', label: 'Rekkehus',         sublabel: 'Rekke- eller kjedehus' },
  { key: 'leilighet_liten', scale: 'neighbourhood', icon: '🏢', label: 'Boligblokk',       sublabel: 'Liten blokk, 6–10 leiligheter' },
  { key: 'leilighet_stor',  scale: 'neighbourhood', icon: '🏙️', label: 'Stort borettslag', sublabel: 'Stor blokk, 20+ leiligheter' },
  { key: 'barneskole',      scale: 'neighbourhood', icon: '🏫', label: 'Skole',            sublabel: 'Barneskole eller ungdomsskole' },
  { key: 'kontorbygg',      scale: 'neighbourhood', icon: '🏗️', label: 'Kontorbygg',       sublabel: 'Kontor eller næringsbygg' },
] as const

type BuildingKey = typeof BUILDING_OPTIONS[number]['key']

export default function Beregn() {
  const { data: config, isLoading: configLoading, error: configError } = useQuery({
    queryKey: ['config'],
    queryFn: api.config,
  })

  const { data: observations, isLoading: obsLoading } = useQuery({
    queryKey: ['observations'],
    queryFn: () => api.observations(365),
    enabled: !!config,
  })

  const [selectedKey, setSelectedKey] = useState<BuildingKey>('enebolig')
  const [buildingCount, setBuildingCount] = useState(10)
  const [population, setPopulation] = useState(4)

  const selectedOption = BUILDING_OPTIONS.find(o => o.key === selectedKey)!

  const handleBuildingChange = (key: BuildingKey) => {
    setSelectedKey(key)
    const preset = config?.building_presets.find(p => p.key === key)
    if (preset) setPopulation(preset.default_people)
  }

  const effectivePreset = useMemo(() => {
    if (!config) return null
    const base = config.building_presets.find(p => p.key === selectedKey)
    if (!base) return null
    if (selectedOption.scale === 'neighbourhood') {
      return {
        ...base,
        label: buildingCount > 1 ? `${buildingCount} × ${base.label}` : base.label,
        roof_area_m2: base.roof_area_m2 * buildingCount,
        default_people: base.default_people * buildingCount,
      }
    }
    return base
  }, [config, selectedKey, selectedOption.scale, buildingCount])

  const totalPrecip = useMemo(
    () => observations?.reduce((s, o) => s + o.precipitation_mm, 0) ?? 0,
    [observations],
  )

  const mutation = useMutation({ mutationFn: api.simulateQuick })

  useEffect(() => {
    if (!effectivePreset || !totalPrecip) return
    mutation.mutate({
      roof_area_m2: effectivePreset.roof_area_m2,
      population,
      total_precipitation_mm: totalPrecip,
    })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [effectivePreset?.roof_area_m2, population, totalPrecip])

  const isNeighbourhood = selectedOption.scale === 'neighbourhood'
  const result = mutation.data

  if (configLoading || obsLoading) return <p style={{ padding: '2rem' }}>Laster data…</p>
  if (configError) return <p className="alert alert-error" style={{ margin: '2rem' }}>Kunne ikke laste konfigurasjon. Er API-serveren oppe?</p>
  if (!config || !observations) return null

  return (
    <>
      <section className="home-hero">
        <h1>Hva skjer med <em>vannet ditt</em><br />når krisen kommer?</h1>
        <p className="home-hero-sub">
          Bergen får over 2&nbsp;000&nbsp;mm nedbør i året — men i en beredskaps&shy;situasjon kan vannforsyningen
          svikte. Finn ut hvor mye regnvann ditt bygg kan samle, og hvor lenge det rekker.
        </p>
        <a href="#konfigurator" className="home-hero-cta">Beregn ditt bygg ↓</a>
        <div className="home-hero-stats">
          <div className="home-hero-stat">
            <div className="home-hero-stat-value">2 000+</div>
            <div className="home-hero-stat-label">mm nedbør/år</div>
          </div>
          <div className="home-hero-stat">
            <div className="home-hero-stat-value">13 L</div>
            <div className="home-hero-stat-label">WHO-minimum/dag</div>
          </div>
          <div className="home-hero-stat">
            <div className="home-hero-stat-value">7 dager</div>
            <div className="home-hero-stat-label">anbefalt reserve</div>
          </div>
        </div>
      </section>

      <div className="configurator" id="konfigurator">
        <h2>Velg bygningstype</h2>
        <p className="configurator-sub">Velg bygget du vil analysere, så beregner vi potensialet automatisk.</p>

        <div className="building-grid">
          {BUILDING_OPTIONS.map(opt => (
            <button
              key={opt.key}
              className={`building-card${selectedKey === opt.key ? ' selected' : ''}`}
              onClick={() => handleBuildingChange(opt.key)}
            >
              <span className="building-card-icon">{opt.icon}</span>
              <span className="building-card-label">{opt.label}</span>
              <span className="building-card-sub">{opt.sublabel}</span>
            </button>
          ))}
        </div>

        {isNeighbourhood && (
          <div className="neighbourhood-count">
            <div className="slider-row">
              <div className="slider-label">
                <span className="slider-label-text">Antall bygg i nabolaget</span>
                <span className="slider-label-value">{buildingCount}</span>
              </div>
              <input
                type="range"
                min={2} max={20} step={1}
                value={buildingCount}
                onChange={e => setBuildingCount(Number(e.target.value))}
              />
            </div>
          </div>
        )}

        <div className="people-slider">
          <div className="slider-row">
            <div className="slider-label">
              <span className="slider-label-text">Antall personer</span>
              <span className="slider-label-value">{fmt(population)}</span>
            </div>
            <input
              type="range"
              min={1} max={isNeighbourhood ? 5000 : 20} step={1}
              value={population}
              onChange={e => setPopulation(Number(e.target.value))}
            />
          </div>
        </div>

        {mutation.isPending && <p style={{ color: '#5a6577', fontSize: '0.9rem' }}>Beregner…</p>}

        {result && (
          <div className="result-section">
            <div
              className="verdict-card"
              style={{
                background: result.color + '18',
                borderColor: result.color,
                marginBottom: '1.5rem',
              }}
            >
              <h3 style={{ color: result.color, fontSize: '1.35rem', fontWeight: 800, margin: '0 0 0.5rem' }}>
                {result.verdict}
              </h3>
              <p style={{ margin: 0, fontSize: '1.05rem', lineHeight: 1.6 }}>
                {effectivePreset?.label} kan samle opp{' '}
                <strong>{fmt(result.annual_liters)} liter</strong> regnvann i året — nok til{' '}
                <strong>{fmt(population)} {population === 1 ? 'person' : 'personer'}</strong> i{' '}
                <strong>{fmt(result.supply_days)} dager</strong> ved en krise.
              </p>
            </div>

            <div className="metric-grid-4">
              <div className="metric-card">
                <div className="metric-card-label">Årlig oppsamling</div>
                <div className="metric-card-value">{fmt(result.annual_liters)} L</div>
              </div>
              <div className="metric-card">
                <div className="metric-card-label">Per dag (snitt)</div>
                <div className="metric-card-value">{fmt(result.metrics.daily_avg_liters)} L</div>
              </div>
              <div className="metric-card">
                <div className="metric-card-label">Daglig behov</div>
                <div className="metric-card-value">{fmt(result.metrics.daily_need_liters)} L</div>
              </div>
              <div className="metric-card highlighted">
                <div className="metric-card-label">Beredskap</div>
                <div className="metric-card-value">{fmt(result.supply_days)} dager</div>
              </div>
            </div>

            <h2 style={{ marginTop: '1.5rem' }}>Anbefalt tankstørrelse</h2>
            <p className="caption">
              Bergen kan ha tørkeperioder på 3–4 uker. Velg størrelse ut fra hvor mange dager uten regn du vil være forberedt på.
            </p>
            <div className="metric-grid-3">
              {result.tank_options.map(opt => (
                <div
                  key={opt.label}
                  className={`tank-card${opt.label === 'Anbefalt' ? ' recommended' : ''}`}
                >
                  <div className="tank-card-label">{opt.label}</div>
                  <div className="tank-card-value">{fmt(opt.liters)} L</div>
                  <div className="tank-card-desc">{opt.description}</div>
                  <div className="tank-card-desc">= {(opt.liters / 1000).toFixed(1)} m³</div>
                </div>
              ))}
            </div>

            <Link
              to="/beredskap"
              className="cta-link"
              state={{
                roof_area_m2: effectivePreset?.roof_area_m2,
                height_m: effectivePreset?.height_m,
                population,
                tank_liters: result.tank_options[1]?.liters,
                num_buildings: isNeighbourhood ? buildingCount : 1,
                building_label: effectivePreset?.label,
                scale: selectedOption.scale,
              }}
            >
              Gå til detaljert simulering →
            </Link>
          </div>
        )}

        {mutation.isError && (
          <p className="alert alert-error">Simulering feilet: {String(mutation.error)}</p>
        )}
      </div>
    </>
  )
}
