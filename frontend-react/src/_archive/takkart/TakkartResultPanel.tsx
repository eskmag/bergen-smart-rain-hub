import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'
import { useTakkart } from '../../context/TakkartContext'
import SimulationChart from '../shared/SimulationChart'
import DrySpellsList from '../shared/DrySpellsList'
import {
  annualCollectionLiters,
  emergencyDays,
  supplyStatus,
  tankRecommendations,
} from '../../lib/rainwater'

function fmt(n: number) {
  return Math.round(n).toLocaleString('nb-NO')
}

const STATUS_LABELS: Record<string, string> = {
  excellent: 'Svært god beredskap',
  good:      'God beredskap',
  moderate:  'Moderat beredskap',
  low:       'Lav beredskap',
}

export default function TakkartResultPanel() {
  const { roofAreaM2, numPeople, setNumPeople, simResult, isSimPending } = useTakkart()
  const { data: config } = useQuery({ queryKey: ['config'], queryFn: api.config })

  if (roofAreaM2 === null) {
    return (
      <div className="t-result-panel t-result-empty">
        <div className="t-empty-icon">
          <svg width="40" height="40" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
            <polyline points="9 22 9 12 15 12 15 22" />
          </svg>
        </div>
        <p className="t-empty-text">Søk opp eller tegn et tak på kartet</p>
        <p className="t-empty-sub">Finn adressen din og få takflaten automatisk, eller velg «Mål manuelt» og tegn et polygon.</p>
      </div>
    )
  }

  if (!config) {
    return (
      <div className="t-result-panel t-result-empty">
        <p className="t-empty-text">Laster…</p>
      </div>
    )
  }

  const lPerDay = config.water_needs['survival_total']
  const annualL = annualCollectionLiters(roofAreaM2, config.defaults)
  const days = emergencyDays(annualL, numPeople, lPerDay)
  const status = supplyStatus(days)
  const tanks = tankRecommendations(numPeople, lPerDay, config.defaults.tank_recommendation_days)
  const dailyAvg = annualL / 365
  const dailyNeed = numPeople * lPerDay

  function handlePeopleStep(delta: number) {
    setNumPeople(Math.max(1, numPeople + delta))
  }

  return (
    <div className="t-result-panel">
      {/* Hero */}
      <div className="t-result-hero">
        <div className="t-rh-eyebrow">Takflate</div>
        <div className="t-rh-area">{fmt(roofAreaM2)} <span className="t-rh-unit">m²</span></div>
      </div>

      {/* Supply card */}
      <div className="t-supply-card">
        <div className="t-sc-number">{fmt(days)}</div>
        <div className="t-sc-label">beredskapsdager per år</div>
        <div className={`t-status-pill ${status}`}>{STATUS_LABELS[status]}</div>
      </div>

      {/* Metrics */}
      <div className="t-metrics-row">
        <div className="t-metric-card">
          <div className="t-mc-label">Årsoppsamling</div>
          <div className="t-mc-val">{fmt(annualL)} <span className="t-mc-unit">L</span></div>
        </div>
        <div className="t-metric-card">
          <div className="t-mc-label">Daglig snitt</div>
          <div className="t-mc-val">{fmt(dailyAvg)} <span className="t-mc-unit">L/dag</span></div>
        </div>
        <div className="t-metric-card">
          <div className="t-mc-label">Daglig behov</div>
          <div className="t-mc-val">{fmt(dailyNeed)} <span className="t-mc-unit">L/dag</span></div>
        </div>
      </div>

      {/* People stepper */}
      <div className="t-people-row">
        <span className="t-people-label">Personer</span>
        <div className="t-stepper">
          <button className="t-stepper-btn" type="button" onClick={() => handlePeopleStep(-1)} aria-label="Færre personer">−</button>
          <span className="t-stepper-val">{numPeople}</span>
          <button className="t-stepper-btn" type="button" onClick={() => handlePeopleStep(1)} aria-label="Flere personer">+</button>
        </div>
        <span className="t-people-note">{lPerDay} L/pers/dag (WHO)</span>
      </div>

      {/* Tank recommendations */}
      <div className="t-tank-section">
        <div className="t-tank-eyebrow">Tankanbefaling</div>
        <div className="t-tank-opts">
          {tanks.map(rec => (
            <div key={rec.days} className="t-tank-opt">
              <div className="t-tank-opt-label">{rec.label}</div>
              <div className="t-tank-opt-liters">{fmt(rec.liters)} L</div>
              <div className="t-tank-opt-days">{rec.days} dager</div>
            </div>
          ))}
        </div>
      </div>

      {/* CTA: send measured roof to full simulator */}
      <div className="t-cta-section">
        <Link
          to={`/beregn?areal=${Math.round(roofAreaM2)}`}
          className="t-cta-btn"
        >
          Simuler med dette taket
          <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path d="M5 12h14M12 5l7 7-7 7" />
          </svg>
        </Link>
        <p className="t-cta-note">Åpner beredskapssimulering med {Math.round(roofAreaM2)} m² forhåndsutfylt</p>
      </div>

      {/* Rich simulation (from backend) */}
      {(simResult || isSimPending) && (
        <>
          <SimulationChart
            series={simResult?.simulation_series}
            loading={isSimPending && !simResult}
            classPrefix="t"
          />

          <DrySpellsList
            spells={simResult?.dry_spells}
            classPrefix="t"
            hideWhenEmpty
            labels={{
              title: 'Sårbare perioder',
              badge: n => `${n} tørkeperioder`,
              days: n => `${n} dager`,
            }}
          />
        </>
      )}
    </div>
  )
}
