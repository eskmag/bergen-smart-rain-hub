import { useQuery } from '@tanstack/react-query'
import {
  AreaChart, Area, XAxis, YAxis,
  CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer,
} from 'recharts'
import { api } from '../../api/client'
import { useBeredskap } from '../../context/BeredskapsContext'
import { BUILDING_OPTIONS } from './buildingTypes'

function fmt(n: number, decimals = 0) {
  return n.toLocaleString('nb-NO', { maximumFractionDigits: decimals })
}

function verdictFor(daysTankEmpty: number) {
  if (daysTankEmpty === 0) return { text: 'Svært god beredskap', dot: '#6EE7B7' }
  if (daysTankEmpty < 14)  return { text: 'Tilstrekkelig beredskap', dot: '#FBBF24' }
  return                          { text: 'Sårbar forsyning', dot: '#FCA5A5' }
}

export default function ResultPanel() {
  const {
    buildingKey,
    simResult, isSimPending,
    population, scale, annualLiters, usageLevel,
  } = useBeredskap()

  const { data: config } = useQuery({ queryKey: ['config'], queryFn: api.config })

  const costsQuery = useQuery({
    queryKey: ['costs', population, scale, Math.round(annualLiters)],
    queryFn: () => api.costs(population, scale, annualLiters),
    enabled: population > 0 && annualLiters > 0,
  })
  const costs = costsQuery.data

  const buildingLabel =
    BUILDING_OPTIONS.find(o => o.key === buildingKey)?.label.toLowerCase() ?? 'bygg'

  const waterNeeds = config?.water_needs ?? {}
  const waterNeedPerDay =
    waterNeeds[usageLevel] ?? (usageLevel === 'normal_usage' ? 150 : 13)
  const dailyNeed = population * waterNeedPerDay

  const summary = simResult?.summary ?? {}
  const supplyDays    = (summary['days_of_survival_supply'] ?? 0) as number
  const totalLiters   = (summary['total_collected_liters'] ?? 0) as number
  const daysTankEmpty = (summary['days_tank_empty'] ?? 0) as number
  const longestDry    = (summary['longest_dry_spell_days'] ?? 0) as number
  const dailyAvg      = totalLiters / 365

  const verdict = verdictFor(daysTankEmpty)
  const loading = isSimPending && !simResult

  const spells = [...(simResult?.dry_spells ?? [])].sort((a, b) => b.days - a.days)
  const maxDays = spells[0]?.days ?? 1
  const topSpells = spells.slice(0, 3)

  return (
    <div className="k-result-panel">
      {/* Hero */}
      <div className="k-result-hero">
        <div className="k-rh-verdict">
          Beredskapsforsyning · {fmt(population)} {population === 1 ? 'person' : 'personer'} · {buildingLabel}
        </div>
        <div className="k-rh-number">{loading ? '—' : fmt(supplyDays)}</div>
        <div className="k-rh-unit">dager med trygg vannforsyning</div>
        {!loading && (
          <div className="k-rh-badge">
            <div className="k-rh-badge-dot" style={{ background: verdict.dot }} />
            {verdict.text}
          </div>
        )}
      </div>

      {/* Metrics */}
      <div className="k-metrics-row">
        <div className="k-metric-card">
          <div className="k-mc-label">Årlig oppsamling</div>
          <div className="k-mc-val">{loading ? '—' : fmt(totalLiters)} <span className="k-mc-unit">L</span></div>
        </div>
        <div className="k-metric-card">
          <div className="k-mc-label">Daglig gjennomsnitt</div>
          <div className="k-mc-val">{loading ? '—' : fmt(dailyAvg)} <span className="k-mc-unit">L/dag</span></div>
        </div>
        <div className="k-metric-card">
          <div className="k-mc-label">Daglig behov</div>
          <div className="k-mc-val">{fmt(dailyNeed)} <span className="k-mc-unit">L/dag</span></div>
        </div>
      </div>

      <p className="k-who-note">
        {waterNeeds['survival_total'] ?? 13} L/person/dag dekker drikke {waterNeeds['drinking'] ?? 3} ·
        hygiene {waterNeeds['sanitation'] ?? 6} · matlaging {waterNeeds['cooking'] ?? 3} ·
        medisin {waterNeeds['medical'] ?? 1} (WHO-minimum)
      </p>

      {/* Tank recommendation */}
      <div className="k-tank-rec">
        <div>
          <div className="k-tr-eyebrow">Anbefalt tankstørrelse</div>
          <div className="k-tr-val">{fmt(dailyNeed * 30)} L</div>
          <div className="k-tr-sub">
            Dekker 30 dager uten nedbør · lengste registrert: {fmt(longestDry)} d
          </div>
        </div>
        <div className="k-tr-options">
          <div className="k-tr-opt">Min: <strong>{fmt(dailyNeed * 7)} L</strong> · 7 dager</div>
          <div className="k-tr-opt">Anbefalt: <strong>{fmt(dailyNeed * 30)} L</strong> · 30 dager</div>
          <div className="k-tr-opt">Robust: <strong>{fmt(dailyNeed * 60)} L</strong> · 60 dager</div>
        </div>
      </div>

      {/* Cost line */}
      {costs && (
        <div className="k-cost-line">
          <div className="k-cl-label">Anslått kostnad</div>
          <div className="k-cl-val">
            ~{fmt(costs.capital)} kr i investering · ~{fmt(costs.annual_op)} kr/år i drift
          </div>
        </div>
      )}

      {/* Chart */}
      <div className="k-chart-card">
        <div className="k-chart-header">
          <span className="k-chart-title">Tanknivå gjennom året</span>
          <div className="k-chart-legend">
            <div className="k-legend-item"><div className="k-legend-dot" style={{ background: '#BFDBF7' }} />Tanknivå</div>
            <div className="k-legend-item"><div className="k-legend-dot" style={{ background: '#C1440E' }} />Kritisk 20 %</div>
          </div>
        </div>
        {loading || !simResult ? (
          <p className="k-placeholder">Simulerer…</p>
        ) : (
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={simResult.simulation_series} margin={{ top: 5, right: 6, left: -18, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#EDF0F3" />
              <XAxis dataKey="date" tickFormatter={d => d.slice(5)} tick={{ fontSize: 10 }} minTickGap={40} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} unit="%" />
              <Tooltip
                formatter={v => [`${Number(v).toFixed(1)} %`, 'Tanknivå']}
                labelFormatter={l => `Dato: ${l}`}
              />
              <ReferenceLine y={20} stroke="#C1440E" strokeDasharray="4 4" />
              <Area type="monotone" dataKey="tank_pct" stroke="var(--k-blue)" fill="#BFDBF7" fillOpacity={0.6} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Dry spells */}
      <div className="k-dry-spells-card">
        <div className="k-ds-header">
          <span className="k-ds-title">Sårbare perioder</span>
          {!loading && (
            <span className="k-ds-badge">{spells.length} tørkeperioder i år</span>
          )}
        </div>
        {loading ? (
          <p className="k-placeholder">Beregner…</p>
        ) : topSpells.length === 0 ? (
          <p className="k-ds-empty">Ingen lengre tørkeperioder funnet.</p>
        ) : (
          topSpells.map((s, i) => (
            <div className="k-ds-row" key={i}>
              <div>
                <div className="k-ds-days">{s.days} dager</div>
                <div className="k-ds-dates">{s.start} — {s.end}</div>
              </div>
              <div className="k-ds-bar-wrap">
                <div className="k-ds-bar">
                  <div className="k-ds-bar-fill" style={{ width: `${(s.days / maxDays) * 100}%` }} />
                </div>
              </div>
              {i === 0
                ? <div className="k-ds-tag-longest">Lengste</div>
                : <div className="k-ds-tag-muted">–</div>}
            </div>
          ))
        )}
      </div>

      {/* Data note */}
      <div className="k-data-note">
        <div className="k-note-dot" />
        Data fra Frost API · Bergen Florida SN50540 · WHO-standard 13 L/person/dag
      </div>
    </div>
  )
}
