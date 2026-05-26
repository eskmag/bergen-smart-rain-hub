import { useQuery } from '@tanstack/react-query'
import {
  AreaChart, Area, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer,
} from 'recharts'
import { api } from '../api/client'
import { MetricCard } from '../components/MetricCard'
import { useBeredskap } from '../context/BeredskapsContext'

function fmt(n: number, decimals = 0) {
  return n.toLocaleString('nb-NO', { maximumFractionDigits: decimals })
}

export default function Simulering() {
  const { simResult, isSimPending, scenario, setScenario } = useBeredskap()
  const { data: config } = useQuery({ queryKey: ['config'], queryFn: api.config })

  const summary = simResult?.summary ?? {}
  const waterNeeds = config?.water_needs ?? {}

  return (
    <>
      <h2>Klimascenario</h2>
      <p className="caption">
        Norske klimafremskrivninger viser økt nedbørsintensitet og lengre tørkeperioder i Vest-Norge.
      </p>
      <div className="radio-group">
        {(config?.climate_scenarios ?? []).map(s => (
          <label key={s.key} className="radio-option">
            <input type="radio" name="scenario" value={s.key}
              checked={scenario === s.key} onChange={() => setScenario(s.key)} />
            {s.label}
          </label>
        ))}
      </div>
      {config && (
        <p className="caption">{config.climate_scenarios.find(s => s.key === scenario)?.description}</p>
      )}

      {simResult?.scenario_comparison && (
        <div className="grid-3" style={{ marginTop: '1rem' }}>
          {simResult.scenario_comparison.map(c => (
            <div key={c.scenario} style={{
              background: c.scenario === scenario ? 'var(--color-primary-light)' : 'var(--color-surface)',
              border: `1px solid ${c.scenario === scenario ? 'var(--color-primary)' : 'var(--color-border)'}`,
              borderRadius: 'var(--radius-md)', padding: '1rem',
            }}>
              <div style={{ fontWeight: c.scenario === scenario ? 700 : 400, marginBottom: '0.5rem' }}>
                {c.label}
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '0.4rem' }}>
                <MetricCard label="Nedbør" value={`${fmt(c.total_precip_mm)} mm`} />
                <MetricCard label="Tørre dager" value={`${c.dry_days}`} />
                <MetricCard label="Lengste tørke" value={`${c.longest_dry_spell} d`} />
              </div>
            </div>
          ))}
        </div>
      )}

      <hr className="section-divider" />

      {isSimPending && <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>Simulerer…</p>}

      {simResult && (
        <>
          <h2>Beredskapsvurdering</h2>
          {summary['days_tank_empty'] === 0 ? (
            <div className="alert alert-success">Tanken gikk aldri tom det siste året — god beredskap!</div>
          ) : (summary['days_tank_empty'] ?? 0) < 14 ? (
            <div className="alert alert-warning">
              Tanken var tom {fmt(summary['days_tank_empty'])} dager. Prøv å øke tankkapasiteten eller legg til flere bygg.
            </div>
          ) : (
            <div className="alert alert-error">
              Tanken var tom {fmt(summary['days_tank_empty'])} dager — utilstrekkelig. Juster parameterne.
            </div>
          )}

          <div className="grid-4">
            <MetricCard label="Årlig oppsamling" value={`${fmt(summary['total_collected_m3'] ?? 0, 1)} m³`} />
            <MetricCard label="Beredskapsforsyning" value={`${fmt(summary['days_of_survival_supply'] ?? 0)} dager`} highlighted />
            <MetricCard label="Dager tank tom" value={`${fmt(summary['days_tank_empty'] ?? 0)}`} />
            <MetricCard label="Lengste tørkeperiode" value={`${fmt(summary['longest_dry_spell_days'] ?? 0)} dager`} />
          </div>

          <hr className="section-divider" />

          <h2>Tanknivå gjennom året</h2>
          <p className="caption">Regn fyller tanken, daglig forbruk tømmer den. Den røde linjen markerer kritisk nivå (20 %).</p>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={simResult.simulation_series} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#DCE3E9" />
              <XAxis dataKey="date" tickFormatter={d => d.slice(5)} tick={{ fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
              <Tooltip
                formatter={(v) => [`${Number(v).toFixed(1)} %`, 'Tanknivå']}
                labelFormatter={l => `Dato: ${l}`}
              />
              <ReferenceLine y={20} stroke="#C1292E" strokeDasharray="4 4" />
              <Area type="monotone" dataKey="tank_pct" stroke="#2B7A8E" fill="#2B7A8E" fillOpacity={0.3} dot={false} />
            </AreaChart>
          </ResponsiveContainer>

          <h2>Dager med vannforsyning igjen</h2>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={simResult.simulation_series} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#DCE3E9" />
              <XAxis dataKey="date" tickFormatter={d => d.slice(5)} tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} unit=" d" />
              <Tooltip
                formatter={(v) => { const n = Number(v); return [n >= 9999 ? '∞' : `${n.toFixed(1)} dager`, 'Dager igjen'] }}
                labelFormatter={l => `Dato: ${l}`}
              />
              <Line type="monotone" dataKey="days_remaining" stroke="#E85D04" dot={false} strokeWidth={1.5} />
            </LineChart>
          </ResponsiveContainer>

          <hr className="section-divider" />

          <h2>Tørkeperioder</h2>
          <p className="caption">Perioder med tre eller flere dager med under 1 mm nedbør — den største risikoen for regnvannsbasert forsyning.</p>
          {simResult.dry_spells.length === 0 ? (
            <p className="alert alert-info">Ingen lengre tørkeperioder funnet.</p>
          ) : (
            <table>
              <thead><tr><th>Start</th><th>Slutt</th><th>Dager</th><th>Total nedbør (mm)</th></tr></thead>
              <tbody>
                {[...simResult.dry_spells].sort((a, b) => b.days - a.days).map((s, i) => (
                  <tr key={i}><td>{s.start}</td><td>{s.end}</td><td>{s.days}</td><td>{s.total_rain_mm.toFixed(1)}</td></tr>
                ))}
              </tbody>
            </table>
          )}

          <hr className="section-divider" />

          <h2>Vannbehov ved krise (WHO-standard)</h2>
          <table>
            <thead><tr><th>Kategori</th><th>Liter/person/dag</th><th>Hva det dekker</th></tr></thead>
            <tbody>
              <tr><td>Drikkevann</td><td>{waterNeeds['drinking'] ?? 3}</td><td>Rent drikkevann for å unngå dehydrering</td></tr>
              <tr><td>Sanitær og hygiene</td><td>{waterNeeds['sanitation'] ?? 6}</td><td>Håndvask, tannpuss og grunnleggende hygiene</td></tr>
              <tr><td>Matlaging</td><td>{waterNeeds['cooking'] ?? 3}</td><td>Vann til koking av mat</td></tr>
              <tr><td>Medisinsk bruk</td><td>{waterNeeds['medical'] ?? 1}</td><td>Sårrengjøring og medisinsk bruk</td></tr>
            </tbody>
          </table>
          <p className="caption">Totalt: {waterNeeds['survival_total'] ?? 13} L/person/dag — absolutt minimum.</p>
        </>
      )}
    </>
  )
}
