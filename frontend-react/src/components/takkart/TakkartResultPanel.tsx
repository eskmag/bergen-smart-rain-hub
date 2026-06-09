import {
  AreaChart, Area, XAxis, YAxis,
  CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer,
} from 'recharts'
import { useTakkart } from '../../context/TakkartContext'
import {
  annualCollectionLiters,
  emergencyDays,
  supplyStatus,
  tankRecommendations,
  WHO_L_PER_PERSON_PER_DAY,
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

  if (roofAreaM2 === null) {
    return (
      <div className="t-result-panel t-result-empty">
        <div className="t-empty-icon">
          <svg width="40" height="40" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
            <polyline points="9 22 9 12 15 12 15 22" />
          </svg>
        </div>
        <p className="t-empty-text">Søk opp eller teikn eit tak på kartet</p>
        <p className="t-empty-sub">Finn adressa di og få takflata automatisk, eller vel «Mål manuelt» og teikn eit polygon.</p>
      </div>
    )
  }

  const annualL = annualCollectionLiters(roofAreaM2)
  const days = emergencyDays(annualL, numPeople)
  const status = supplyStatus(days)
  const tanks = tankRecommendations(numPeople)
  const dailyAvg = annualL / 365
  const dailyNeed = numPeople * WHO_L_PER_PERSON_PER_DAY

  function handlePeopleStep(delta: number) {
    setNumPeople(Math.max(1, numPeople + delta))
  }

  const spells = [...(simResult?.dry_spells ?? [])].sort((a, b) => b.days - a.days)
  const maxDryDays = spells[0]?.days ?? 1
  const topSpells = spells.slice(0, 3)

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
        <div className="t-sc-label">beredskapsdagar per år</div>
        <div className={`t-status-pill ${status}`}>{STATUS_LABELS[status]}</div>
      </div>

      {/* Metrics */}
      <div className="t-metrics-row">
        <div className="t-metric-card">
          <div className="t-mc-label">Årsoppsamling</div>
          <div className="t-mc-val">{fmt(annualL)} <span className="t-mc-unit">L</span></div>
        </div>
        <div className="t-metric-card">
          <div className="t-mc-label">Dagleg snitt</div>
          <div className="t-mc-val">{fmt(dailyAvg)} <span className="t-mc-unit">L/dag</span></div>
        </div>
        <div className="t-metric-card">
          <div className="t-mc-label">Dagleg behov</div>
          <div className="t-mc-val">{fmt(dailyNeed)} <span className="t-mc-unit">L/dag</span></div>
        </div>
      </div>

      {/* People stepper */}
      <div className="t-people-row">
        <span className="t-people-label">Personar</span>
        <div className="t-stepper">
          <button className="t-stepper-btn" type="button" onClick={() => handlePeopleStep(-1)} aria-label="Færre personar">−</button>
          <span className="t-stepper-val">{numPeople}</span>
          <button className="t-stepper-btn" type="button" onClick={() => handlePeopleStep(1)} aria-label="Fleire personar">+</button>
        </div>
        <span className="t-people-note">{WHO_L_PER_PERSON_PER_DAY} L/pers/dag (WHO)</span>
      </div>

      {/* Tank recommendations */}
      <div className="t-tank-section">
        <div className="t-tank-eyebrow">Tankanbefaling</div>
        <div className="t-tank-opts">
          {tanks.map(rec => (
            <div key={rec.days} className="t-tank-opt">
              <div className="t-tank-opt-label">{rec.label}</div>
              <div className="t-tank-opt-liters">{fmt(rec.liters)} L</div>
              <div className="t-tank-opt-days">{rec.days} dagar</div>
            </div>
          ))}
        </div>
      </div>

      {/* Rich simulation (from backend) */}
      {(simResult || isSimPending) && (
        <>
          <div className="t-chart-card">
            <div className="t-chart-header">
              <span className="t-chart-title">Tanknivå gjennom året</span>
              <div className="t-chart-legend">
                <div className="t-legend-item"><div className="t-legend-dot" style={{ background: '#BFDBF7' }} />Tanknivå</div>
                <div className="t-legend-item"><div className="t-legend-dot" style={{ background: '#C1440E' }} />Kritisk 20 %</div>
              </div>
            </div>
            {isSimPending && !simResult ? (
              <p className="t-placeholder">Simulerer…</p>
            ) : (
              <ResponsiveContainer width="100%" height={160}>
                <AreaChart data={simResult!.simulation_series} margin={{ top: 5, right: 6, left: -18, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#EDF0F3" />
                  <XAxis dataKey="date" tickFormatter={d => d.slice(5)} tick={{ fontSize: 10 }} minTickGap={40} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} unit="%" />
                  <Tooltip
                    formatter={v => [`${Number(v).toFixed(1)} %`, 'Tanknivå']}
                    labelFormatter={l => `Dato: ${l}`}
                  />
                  <ReferenceLine y={20} stroke="#C1440E" strokeDasharray="4 4" />
                  <Area type="monotone" dataKey="tank_pct" stroke="var(--color-primary)" fill="#BFDBF7" fillOpacity={0.6} dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>

          {topSpells.length > 0 && (
            <div className="t-dry-spells-card">
              <div className="t-ds-header">
                <span className="t-ds-title">Sårbare periodar</span>
                <span className="t-ds-badge">{spells.length} tørkeperiodar</span>
              </div>
              {topSpells.map((s, i) => (
                <div className="t-ds-row" key={i}>
                  <div>
                    <div className="t-ds-days">{s.days} dagar</div>
                    <div className="t-ds-dates">{s.start} — {s.end}</div>
                  </div>
                  <div className="t-ds-bar-wrap">
                    <div className="t-ds-bar">
                      <div className="t-ds-bar-fill" style={{ width: `${(s.days / maxDryDays) * 100}%` }} />
                    </div>
                  </div>
                  {i === 0
                    ? <div className="t-ds-tag-longest">Lengste</div>
                    : <div className="t-ds-tag-muted">–</div>}
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
