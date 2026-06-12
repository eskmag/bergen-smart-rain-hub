import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'
import { useBeredskap } from '../../context/BeredskapsContext'
import { BUILDING_OPTIONS } from './buildingTypes'

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

function clampTank(v: number) {
  return Math.min(TANK_MAX, Math.max(TANK_MIN, Math.round(v / 500) * 500))
}

export default function InputPanel() {
  const {
    buildingKey: selectedKey, setBuildingKey,
    population, setPopulation,
    setRoofPerBuilding, setHeightM, setNumBuildings,
    setScale,
    tankLiters, setTankLiters,
    efficiency, setEfficiency,
    usageLevel, setUsageLevel,
    roofMaterial, setRoofMaterial,
  } = useBeredskap()

  const { data: config } = useQuery({ queryKey: ['config'], queryFn: api.config })
  const [advancedOpen, setAdvancedOpen] = useState(false)

  const waterNeedPerDay =
    config?.water_needs?.[usageLevel] ?? (usageLevel === 'normal_usage' ? 150 : 13)
  const dailyNeed = population * waterNeedPerDay

  function handleBuildingSelect(key: string) {
    const preset = config?.building_presets.find(p => p.key === key)
    const opt = BUILDING_OPTIONS.find(o => o.key === key)!
    setBuildingKey(key)
    if (preset) {
      setRoofPerBuilding(preset.roof_area_m2)
      setHeightM(preset.height_m)
      setPopulation(preset.default_people)
    }
    setScale(opt.scale)
    setNumBuildings(1)
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

      {/* Building type */}
      <div className="k-input-section">
        <div className="k-input-label">
          Bygningstype
          <span className="k-input-hint">— velg det som passer best</span>
        </div>
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
        </div>
      )}
    </div>
  )
}
