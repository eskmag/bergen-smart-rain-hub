import { useState, useMemo, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { api } from '../api/client'
import type { BuildingPreset, InfrastructureFacility } from '../api/client'
import { MetricCard } from '../components/MetricCard'

function fmt(n: number, decimals = 0) {
  return n.toLocaleString('nb-NO', { maximumFractionDigits: decimals })
}

export default function Home() {
  const { data: config, isLoading: configLoading, error: configError } = useQuery({
    queryKey: ['config'],
    queryFn: api.config,
  })

  const { data: observations, isLoading: obsLoading } = useQuery({
    queryKey: ['observations'],
    queryFn: () => api.observations(365),
    enabled: !!config,
  })

  const [scaleKey, setScaleKey] = useState('household')
  const [selectedPresetKey, setSelectedPresetKey] = useState('enebolig')
  const [selectedFacilityKey, setSelectedFacilityKey] = useState('haukeland')
  const [buildingCount, setBuildingCount] = useState(10)
  const [population, setPopulation] = useState(4)

  const handlePresetChange = (key: string) => {
    setSelectedPresetKey(key)
    const preset = config?.building_presets.find(p => p.key === key)
    if (preset) setPopulation(preset.default_people)
  }

  const handleFacilityChange = (key: string) => {
    setSelectedFacilityKey(key)
    const fac = config?.infrastructure_facilities.find(f => f.key === key)
    if (fac) setPopulation(fac.default_people)
  }

  const handleScaleChange = (key: string) => {
    setScaleKey(key)
    if (key === 'infrastructure') {
      const fac = config?.infrastructure_facilities[0]
      if (fac) { setSelectedFacilityKey(fac.key); setPopulation(fac.default_people) }
    } else {
      const presetKeys = config?.scale_presets[key] ?? []
      const firstKey = presetKeys[0] ?? 'enebolig'
      handlePresetChange(firstKey)
    }
  }

  const effectivePreset = useMemo((): (BuildingPreset | InfrastructureFacility) & { building_count?: number } | null => {
    if (!config) return null
    if (scaleKey === 'infrastructure') {
      return config.infrastructure_facilities.find(f => f.key === selectedFacilityKey) ?? null
    }
    const base = config.building_presets.find(p => p.key === selectedPresetKey)
    if (!base) return null
    if (scaleKey === 'neighbourhood') {
      return {
        ...base,
        label: buildingCount > 1 ? `${buildingCount} × ${base.label}` : base.label,
        roof_area_m2: base.roof_area_m2 * buildingCount,
        default_people: base.default_people * buildingCount,
        building_count: buildingCount,
      }
    }
    return base
  }, [config, scaleKey, selectedPresetKey, selectedFacilityKey, buildingCount])

  const totalPrecip = useMemo(
    () => observations?.reduce((s, o) => s + o.precipitation_mm, 0) ?? 0,
    [observations],
  )

  const mutation = useMutation({
    mutationFn: api.simulateQuick,
  })

  useEffect(() => {
    if (!effectivePreset || !totalPrecip) return
    mutation.mutate({
      roof_area_m2: effectivePreset.roof_area_m2,
      population,
      total_precipitation_mm: totalPrecip,
    })
  // mutation is intentionally excluded — calling mutate never changes identity
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [effectivePreset?.roof_area_m2, population, totalPrecip])

  if (configLoading || obsLoading) return <p>Laster data…</p>
  if (configError) return <p className="alert alert-error">Kunne ikke laste konfigurasjon. Er API-serveren oppe?</p>
  if (!config || !observations) return null

  const scale = config.scales.find(s => s.key === scaleKey)!
  const presetKeysForScale = config.scale_presets[scaleKey] ?? []

  const result = mutation.data

  return (
    <>
      <h1>Bergen Smart Rain Hub</h1>
      <p className="subtitle">
        Finn ut hvor mye regnvann ditt bygg kan samle opp, og hvor lenge det rekker i en krisesituasjon.
      </p>

      <h2>1. Velg skala</h2>
      <div className="radio-group">
        {config.scales.map(s => (
          <label key={s.key} className="radio-option">
            <input
              type="radio"
              name="scale"
              value={s.key}
              checked={scaleKey === s.key}
              onChange={() => handleScaleChange(s.key)}
            />
            {s.label}
          </label>
        ))}
      </div>
      <p className="caption">{scale.description}</p>

      <h2>2. Velg bygningstype</h2>
      {scaleKey === 'infrastructure' ? (
        <div className="radio-group">
          {config.infrastructure_facilities.map(f => (
            <label key={f.key} className="radio-option">
              <input
                type="radio"
                name="facility"
                value={f.key}
                checked={selectedFacilityKey === f.key}
                onChange={() => handleFacilityChange(f.key)}
              />
              {f.label}
            </label>
          ))}
        </div>
      ) : (
        <div className="radio-group">
          {presetKeysForScale.map(k => {
            const p = config.building_presets.find(bp => bp.key === k)!
            return (
              <label key={k} className="radio-option">
                <input
                  type="radio"
                  name="preset"
                  value={k}
                  checked={selectedPresetKey === k}
                  onChange={() => handlePresetChange(k)}
                />
                {p.label}
              </label>
            )
          })}
        </div>
      )}
      {effectivePreset && <p className="caption">{effectivePreset.description}</p>}

      {scaleKey === 'neighbourhood' && (
        <div className="slider-row" style={{ maxWidth: 400 }}>
          <label>Antall bygg i nabolaget: <strong>{buildingCount}</strong></label>
          <input
            type="range"
            min={2} max={20} step={1}
            value={buildingCount}
            onChange={e => setBuildingCount(Number(e.target.value))}
          />
        </div>
      )}

      <h2>3. Hvor mange personer?</h2>
      <div className="slider-row" style={{ maxWidth: 500 }}>
        <label>Antall personer: <strong>{fmt(population)}</strong></label>
        <input
          type="range"
          min={1} max={5000} step={1}
          value={population}
          onChange={e => setPopulation(Number(e.target.value))}
        />
      </div>

      <hr className="section-divider" />

      {mutation.isPending && <p>Beregner…</p>}

      {result && (
        <>
          <div
            className="hero-card"
            style={{
              background: result.color + '15',
              borderColor: result.color,
            }}
          >
            <h2 style={{ color: result.color }}>{result.verdict}</h2>
            <p>
              Ditt <strong>{effectivePreset?.label.toLowerCase()}</strong> kan samle opp{' '}
              <strong>{fmt(result.annual_liters)} liter</strong> regnvann i året — nok til å forsyne{' '}
              <strong>{fmt(population)} {population === 1 ? 'person' : 'personer'}</strong> i{' '}
              <strong>{fmt(result.supply_days)} dager</strong> ved en vannkrise.
            </p>
          </div>

          <div className="grid-4">
            <MetricCard label="Årlig oppsamling" value={`${fmt(result.annual_liters)} L`} />
            <MetricCard label="Per dag (snitt)" value={`${fmt(result.metrics.daily_avg_liters)} L`} />
            <MetricCard label="Daglig behov" value={`${fmt(result.metrics.daily_need_liters)} L`} />
            <MetricCard label="Beredskap" value={`${fmt(result.supply_days)} dager`} highlighted />
          </div>

          <hr className="section-divider" />
          <h2>Anbefalt tankstørrelse</h2>
          <p className="caption">
            Bergen kan ha tørkeperioder på opptil 3–4 uker. Størrelsen avhenger av hvor mange dager uten regn du vil
            være forberedt på.
          </p>
          <div className="grid-3">
            {result.tank_options.map(opt => (
              <div
                key={opt.label}
                style={{
                  background: opt.label === 'Anbefalt' ? '#e8f4f8' : '#f8f9fa',
                  border: `1px solid ${opt.label === 'Anbefalt' ? '#2E86AB' : '#dee2e6'}`,
                  borderRadius: '0.5rem',
                  padding: '1rem',
                }}
              >
                <div style={{ fontWeight: opt.label === 'Anbefalt' ? 700 : 400 }}>{opt.label}</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, margin: '0.25rem 0' }}>
                  {fmt(opt.liters)} L
                </div>
                <div className="caption">{opt.description}</div>
                <div className="caption">= {(opt.liters / 1000).toFixed(1)} m³</div>
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
              num_buildings: scaleKey === 'neighbourhood' ? buildingCount : 1,
              building_label: effectivePreset?.label,
              scale: scaleKey,
            }}
          >
            Gå til detaljert simulering →
          </Link>
        </>
      )}

      {mutation.isError && (
        <p className="alert alert-error">Simulering feilet: {String(mutation.error)}</p>
      )}
    </>
  )
}
