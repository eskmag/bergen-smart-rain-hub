import { Outlet, NavLink } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import { useBeredskap } from '../context/BeredskapsContext'

function fmt(n: number, decimals = 0) {
  return n.toLocaleString('nb-NO', { maximumFractionDigits: decimals })
}

function ControlsPanel() {
  const {
    roofPerBuilding, setRoofPerBuilding,
    numBuildings, setNumBuildings,
    population, setPopulation,
    tankLiters, setTankLiters,
    efficiency, setEfficiency,
    usageLevel, setUsageLevel,
    scale, setScale,
  } = useBeredskap()

  const { data: config } = useQuery({ queryKey: ['config'], queryFn: api.config })
  const waterNeeds = config?.water_needs ?? {}

  return (
    <div className="controls-panel">
      <div className="grid-3" style={{ margin: 0 }}>
        <div>
          <div className="slider-row">
            <div className="slider-label">
              <span className="slider-label-text">Takareal per bygg (m²)</span>
              <span className="slider-label-value">{fmt(roofPerBuilding)}</span>
            </div>
            <input type="range" min={50} max={30000} step={50}
              value={roofPerBuilding} onChange={e => setRoofPerBuilding(Number(e.target.value))} />
          </div>
          <div className="slider-row">
            <div className="slider-label">
              <span className="slider-label-text">Antall bygg</span>
              <span className="slider-label-value">{numBuildings}</span>
            </div>
            <input type="range" min={1} max={50} step={1}
              value={numBuildings} onChange={e => setNumBuildings(Number(e.target.value))} />
          </div>
        </div>
        <div>
          <div className="slider-row">
            <div className="slider-label">
              <span className="slider-label-text">Befolkning</span>
              <span className="slider-label-value">{fmt(population)}</span>
            </div>
            <input type="range" min={1} max={5000} step={1}
              value={population} onChange={e => setPopulation(Number(e.target.value))} />
          </div>
          <div className="slider-row">
            <div className="slider-label">
              <span className="slider-label-text">Tankkapasitet (liter)</span>
              <span className="slider-label-value">{fmt(tankLiters)}</span>
            </div>
            <input type="range" min={1000} max={500000} step={1000}
              value={tankLiters} onChange={e => setTankLiters(Number(e.target.value))} />
          </div>
        </div>
        <div>
          <div className="slider-row">
            <div className="slider-label">
              <span className="slider-label-text">Effektivitet</span>
              <span className="slider-label-value">{efficiency} %</span>
            </div>
            <input type="range" min={50} max={95} step={1}
              value={efficiency} onChange={e => setEfficiency(Number(e.target.value))} />
          </div>
          <div className="slider-row">
            <span className="slider-label-text">Forbruksnivå</span>
            <select value={usageLevel} onChange={e => setUsageLevel(e.target.value)} style={{ marginTop: '0.4rem' }}>
              <option value="survival_total">Beredskap ({waterNeeds['survival_total'] ?? 13} L/p/dag)</option>
              <option value="normal_usage">Normal ({waterNeeds['normal_usage'] ?? 150} L/p/dag)</option>
            </select>
          </div>
          <div className="slider-row">
            <span className="slider-label-text">Skala</span>
            <select value={scale} onChange={e => setScale(e.target.value)} style={{ marginTop: '0.4rem' }}>
              {(config?.scales ?? []).map(s => (
                <option key={s.key} value={s.key}>{s.label}</option>
              ))}
            </select>
          </div>
        </div>
      </div>
    </div>
  )
}

function tabClass({ isActive }: { isActive: boolean }) {
  return isActive ? 'tab-btn active' : 'tab-btn'
}

export default function BeredskapsLayout() {
  return (
    <div className="page-content">
      <h1>Vannberedskap</h1>
      <p className="subtitle">
        Simuler regnvannsoppsamling som beredskapsressurs — for husholdning, borettslag eller nabolag.
      </p>

      <ControlsPanel />

      <div className="tab-bar">
        <NavLink to="/beredskap" end className={tabClass}>Simulering</NavLink>
        <NavLink to="/beredskap/risiko" className={tabClass}>Risikovurdering</NavLink>
        <NavLink to="/beredskap/kostnader" className={tabClass}>Kostnadsanalyse</NavLink>
      </div>

      <Outlet />
    </div>
  )
}
