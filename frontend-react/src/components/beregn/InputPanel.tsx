import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'
import { useBeredskap } from '../../context/BeredskapsContext'
import { BUILDING_OPTIONS } from './buildingTypes'
import RoofMapModal from './RoofMapModal'
import type { Feature, Polygon } from 'geojson'

function fmt(n: number) {
  return n.toLocaleString('nb-NO', { maximumFractionDigits: 0 })
}

// People stepper increment scales with the current count so large
// buildings (schools, halls) aren't adjusted one person at a time.
function stepFor(v: number) {
  if (v < 20) return 1
  if (v < 200) return 10
  return 25
}

// Slider bounds — pure UI constraints, not domain values
const TANK_MIN = 500
const TANK_MAX = 100000

// Labels for the tank tiers served by /api/config (defaults.tank_recommendation_days)
const TANK_PRESET_LABELS = ['1 uke', '30 dager', '2 mnd']

const ROOF_SOURCES = [
  { key: 'preset', label: 'Bygningstype' },
  { key: 'map', label: 'Kart' },
] as const

function clampTank(v: number) {
  return Math.min(TANK_MAX, Math.max(TANK_MIN, Math.round(v / 500) * 500))
}

export default function InputPanel() {
  const {
    buildingKey: selectedKey, setBuildingKey,
    population, setPopulation,
    roofPerBuilding, setRoofPerBuilding, setHeightM, setNumBuildings,
    roofSource, setRoofSource,
    polygon, setPolygon,
    tankLiters, setTankLiters,
    efficiency, setEfficiency,
    usageLevel, setUsageLevel,
    roofMaterial, setRoofMaterial,
    station, setStation,
  } = useBeredskap()

  const { data: config } = useQuery({ queryKey: ['config'], queryFn: api.config })
  const [advancedOpen, setAdvancedOpen] = useState(false)
  const [mapOpen, setMapOpen] = useState(false)

  const waterNeedPerDay =
    config?.water_needs?.[usageLevel] ?? (usageLevel === 'normal_usage' ? 150 : 13)
  const dailyNeed = population * waterNeedPerDay

  function handleBuildingSelect(key: string) {
    const preset = config?.building_presets.find(p => p.key === key)
    setBuildingKey(key)
    setRoofSource('preset')
    setPolygon(null)
    if (preset) {
      setRoofPerBuilding(preset.roof_area_m2)
      setHeightM(preset.height_m)
      setPopulation(preset.default_people)
    }
    setNumBuildings(1)
  }

  function handleUseRoof(feature: Feature<Polygon>) {
    setPolygon(feature)  // context derives area + sets roofSource='map'
    setMapOpen(false)
  }

  function adjustPeople(dir: 1 | -1) {
    const next = Math.max(1, population + dir * stepFor(population))
    setPopulation(next)
  }

  const tankPresets = (config?.defaults.tank_recommendation_days ?? []).map((days, i) => ({
    label: TANK_PRESET_LABELS[i] ?? `${days} dager`,
    days,
  }))

  const tankPct = ((tankLiters - TANK_MIN) / (TANK_MAX - TANK_MIN)) * 100
  const activePreset = tankPresets.find(p => clampTank(dailyNeed * p.days) === tankLiters)

  return (
    <div className="k-input-panel">
      <p className="k-panel-eyebrow">Konfigurer beregningen</p>

      {/* Roof area — the source of truth */}
      <div className="k-input-section">
        <div className="k-input-label">
          Takareal
          <span className="k-input-hint">— grunnlaget for hele beregningen</span>
        </div>

        <div className="k-roof-tabs">
          {ROOF_SOURCES.map(s => (
            <button
              key={s.key}
              className={`k-roof-tab${roofSource === s.key ? ' active' : ''}`}
              onClick={() => setRoofSource(s.key)}
            >
              {s.label}
            </button>
          ))}
        </div>

        <div className="k-roof-area-field">
          <span className="k-roof-area-value">{fmt(roofPerBuilding)}</span>
          <span className="k-roof-area-unit">m²</span>
        </div>

        {roofSource === 'map' && (
          <div className="k-roof-map-row">
            <button className="k-roof-map-btn" onClick={() => setMapOpen(true)}>
              {polygon ? 'Endre taket på kart' : 'Mål på kart'}
              <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </button>
            {polygon && (
              <span className="k-roof-map-hint">Takflate hentet fra kart</span>
            )}
          </div>
        )}

        {roofSource === 'preset' && (
          <div className="k-building-grid">
            {BUILDING_OPTIONS.map(opt => (
              <button
                key={opt.key}
                className={`k-building-opt${selectedKey === opt.key ? ' selected' : ''}`}
                onClick={() => handleBuildingSelect(opt.key)}
              >
                <span className="k-bo-icon">{opt.icon}</span>
                <span className="k-bo-name">{opt.label}</span>
                <span className="k-bo-detail">{opt.detail}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* People */}
      <div className="k-input-section">
        <div className="k-input-label">Antall personer</div>
        <div className="k-people-row">
          <div className="k-people-stepper">
            <button className="k-stepper-btn" onClick={() => adjustPeople(-1)} disabled={population <= 1}>−</button>
            <div className="k-stepper-val">{fmt(population)}</div>
            <button className="k-stepper-btn" onClick={() => adjustPeople(1)}>+</button>
          </div>
          <span className="k-stepper-unit">personer skal forsynes</span>
        </div>
      </div>

      {/* Tank */}
      <div className="k-input-section">
        <div className="k-input-label">Tankstørrelse</div>
        <div className="k-tank-display">
          <span className="k-tank-val">{fmt(tankLiters)}</span>
          <span className="k-tank-unit">liter</span>
        </div>
        <input
          className="k-tank-range"
          type="range"
          min={TANK_MIN}
          max={TANK_MAX}
          step={500}
          value={tankLiters}
          onChange={e => setTankLiters(Number(e.target.value))}
          style={{ background: `linear-gradient(to right, var(--k-blue) ${tankPct}%, var(--k-surface) ${tankPct}%)` }}
        />
        <div className="k-slider-labels">
          <span>{fmt(TANK_MIN)} L</span>
          <span>25 000 L</span>
          <span>{fmt(TANK_MAX)} L</span>
        </div>
        <div className="k-tank-presets">
          {tankPresets.map(p => (
            <button
              key={p.label}
              className={`k-tank-preset${activePreset?.label === p.label ? ' active' : ''}`}
              onClick={() => setTankLiters(clampTank(dailyNeed * p.days))}
            >
              {p.label}{activePreset?.label === p.label ? ' ✓' : ''}
            </button>
          ))}
          <span className={`k-tank-preset${!activePreset ? ' active' : ''}`}>Tilpasset</span>
        </div>
      </div>

      {/* Advanced */}
      <button className="k-advanced-toggle" onClick={() => setAdvancedOpen(v => !v)}>
        <div className="k-toggle-icon">{advancedOpen ? '−' : '+'}</div>
        Avanserte innstillinger
        <span className="k-advanced-meta">effektivitet, forbruksnivå</span>
      </button>

      {advancedOpen && (
        <div className="k-advanced-body">
          <div className="k-adv-row">
            <div className="k-adv-label">
              <span>Oppsamlingseffektivitet</span>
              <strong>{efficiency} %</strong>
            </div>
            <input
              className="k-adv-range"
              type="range" min={50} max={95} step={1}
              value={efficiency}
              onChange={e => setEfficiency(Number(e.target.value))}
            />
          </div>
          <div className="k-adv-row">
            <div className="k-adv-label"><span>Forbruksnivå</span></div>
            <select
              className="k-adv-select"
              value={usageLevel}
              onChange={e => setUsageLevel(e.target.value)}
            >
              <option value="survival_total">Beredskap ({config?.water_needs?.['survival_total'] ?? 13} L/p/dag)</option>
              <option value="normal_usage">Normal ({config?.water_needs?.['normal_usage'] ?? 150} L/p/dag)</option>
            </select>
          </div>
          <div className="k-adv-row">
            <div className="k-adv-label"><span>Takmateriale</span></div>
            <select
              className="k-adv-select"
              value={roofMaterial}
              onChange={e => setRoofMaterial(e.target.value)}
            >
              {(config?.roof_materials ?? []).map(m => (
                <option key={m.key} value={m.key}>{m.label}</option>
              ))}
            </select>
          </div>
          <div className="k-adv-row">
            <div className="k-adv-label"><span>Værstasjon</span></div>
            <select
              className="k-adv-select"
              value={station}
              onChange={e => setStation(e.target.value)}
            >
              {(config?.stations ?? []).map(s => (
                <option key={s.id} value={s.id} title={s.note}>{s.label}</option>
              ))}
            </select>
          </div>
        </div>
      )}

      {mapOpen && (
        <RoofMapModal
          initialPolygon={polygon}
          onUse={handleUseRoof}
          onClose={() => setMapOpen(false)}
        />
      )}
    </div>
  )
}
