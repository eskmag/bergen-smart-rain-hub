import { useState, useEffect, useMemo } from 'react'
import { useLocation } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  AreaChart, Area, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer,
} from 'recharts'
import { api } from '../api/client'
import { MetricCard } from '../components/MetricCard'

type Tab = 'simulering' | 'risiko' | 'kostnader'

function fmt(n: number, decimals = 0) {
  return n.toLocaleString('nb-NO', { maximumFractionDigits: decimals })
}

const SEVERITY_COLORS: Record<string, string> = {
  Kritisk: '#C1292E',
  Høy: '#E8963E',
  Middels: '#2B7A8E',
}

interface NavState {
  roof_area_m2?: number
  height_m?: number
  population?: number
  tank_liters?: number
  num_buildings?: number
  building_label?: string
  scale?: string
}

export default function Vannberedskap() {
  const location = useLocation()
  const nav = (location.state ?? {}) as NavState

  const { data: config } = useQuery({ queryKey: ['config'], queryFn: api.config })

  const [tab, setTab] = useState<Tab>('simulering')
  const [roofPerBuilding, setRoofPerBuilding] = useState(nav.roof_area_m2 ?? 120)
  const [numBuildings, setNumBuildings] = useState(nav.num_buildings ?? 1)
  const [population, setPopulation] = useState(nav.population ?? 4)
  const [tankLiters, setTankLiters] = useState(nav.tank_liters ?? 5000)
  const [efficiency, setEfficiency] = useState(85)
  const [usageLevel, setUsageLevel] = useState('survival_total')
  const [scenario, setScenario] = useState('historical')
  const [scale, setScale] = useState(nav.scale ?? 'household')
  const [openRisk, setOpenRisk] = useState<string | null>(null)
  const [openCcp, setOpenCcp] = useState<string | null>(null)

  const heightM = nav.height_m ?? 6

  // ── Simulation ────────────────────────────────────────────────────────────
  const simMutation = useMutation({ mutationFn: api.simulateBeredskap })

  const runSim = () => {
    const buildings = Array.from({ length: numBuildings }, (_, i) => ({
      label: `Bygg ${i + 1}`,
      roof_area_m2: roofPerBuilding,
      height_m: heightM,
    }))
    simMutation.mutate({
      buildings,
      tank_liters: tankLiters,
      population,
      efficiency: efficiency / 100,
      usage_level: usageLevel,
      climate_scenario: scenario,
    })
  }

  useEffect(() => { runSim() }, [roofPerBuilding, numBuildings, population, tankLiters, efficiency, usageLevel, scenario])

  const simResult = simMutation.data
  const summary = simResult?.summary ?? {}

  // ── Risk assessment (auto-triggers after simulation) ──────────────────────
  const riskMutation = useMutation({ mutationFn: api.assessRisk })

  useEffect(() => {
    if (!simResult) return
    riskMutation.mutate({
      tank_liters: tankLiters,
      population,
      roof_area_m2: roofPerBuilding * numBuildings,
      scale,
      days_tank_empty: simResult.summary['days_tank_empty'] ?? 0,
      longest_dry_spell: simResult.summary['longest_dry_spell_days'] ?? 0,
    })
  }, [simResult, scale])

  // ── Cost analysis ─────────────────────────────────────────────────────────
  const annualLiters = useMemo(
    () => (simResult?.summary['total_collected_liters'] ?? 0) as number,
    [simResult],
  )

  const costsQuery = useQuery({
    queryKey: ['costs', population, scale, Math.round(annualLiters)],
    queryFn: () => api.costs(population, scale, annualLiters),
    enabled: population > 0,
  })

  const costs = costsQuery.data
  const waterNeeds = config?.water_needs ?? {}

  // Lifecycle chart data
  const lifecycleData = useMemo(() => {
    if (!costs) return []
    return Array.from({ length: 31 }, (_, y) => ({
      år: y,
      kostnad: costs.capital + costs.annual_op * y,
    }))
  }, [costs])

  return (
    <div className="page-content">
      <h1>Vannberedskap</h1>
      <p className="subtitle">
        Simuler regnvannsoppsamling som beredskapsressurs — for husholdning, borettslag eller nabolag.
      </p>

      {/* ── Tab bar ── */}
      <div className="tab-bar">
        {(['simulering', 'risiko', 'kostnader'] as Tab[]).map(t => (
          <button
            key={t}
            className={`tab-btn${tab === t ? ' active' : ''}`}
            onClick={() => setTab(t)}
          >
            {t === 'simulering' ? 'Simulering' : t === 'risiko' ? 'Risikovurdering' : 'Kostnadsanalyse'}
          </button>
        ))}
      </div>

      {/* ── Shared controls (always visible) ── */}
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

      <hr className="section-divider" />

      {/* ══════════════════════════════════════════════════════════════════════
          TAB: SIMULERING
         ══════════════════════════════════════════════════════════════════════ */}
      {tab === 'simulering' && (
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

          {simMutation.isPending && <p>Simulerer…</p>}

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
                  <ReferenceLine y={20} stroke="red" strokeDasharray="4 4" />
                  <Area type="monotone" dataKey="tank_pct" stroke="#2B7A8E" fill="#2B7A8E" fillOpacity={0.35} dot={false} />
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
      )}

      {/* ══════════════════════════════════════════════════════════════════════
          TAB: RISIKOVURDERING
         ══════════════════════════════════════════════════════════════════════ */}
      {tab === 'risiko' && (
        <>
          <p className="subtitle" style={{ marginBottom: '1rem' }}>
            Systematisk risikovurdering basert på norske og internasjonale standarder, tilpasset ditt scenario.
          </p>

          {(riskMutation.isPending || !riskMutation.data) && !riskMutation.isError && (
            <p>{simResult ? 'Vurderer risikoer…' : 'Kjør simulering først (Simulering-fanen).'}</p>
          )}

          {riskMutation.data && (
            <>
              <h2>Risikoer for ditt scenario</h2>
              <p className="caption">Rangert etter relevans for ditt oppsett. Klikk for å se detaljer og tiltak.</p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', margin: '1rem 0' }}>
                {riskMutation.data.assessed_risks.map(risk => {
                  const color = SEVERITY_COLORS[risk.overall] ?? '#666'
                  const isOpen = openRisk === risk.name
                  return (
                    <div key={risk.name} style={{ border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
                      <button
                        onClick={() => setOpenRisk(isOpen ? null : risk.name)}
                        style={{
                          width: '100%', textAlign: 'left', padding: '0.75rem 1rem',
                          background: 'var(--color-surface)', border: 'none', cursor: 'pointer',
                          display: 'flex', alignItems: 'center', gap: '0.75rem',
                          fontFamily: 'var(--font-body)',
                        }}
                      >
                        <span style={{
                          background: color, color: '#fff', padding: '2px 8px',
                          borderRadius: '4px', fontSize: '0.8rem', whiteSpace: 'nowrap',
                        }}>{risk.overall}</span>
                        <span style={{ fontWeight: 500 }}>{risk.name}</span>
                        <span style={{ marginLeft: 'auto', color: 'var(--color-text-muted)' }}>{isOpen ? '▲' : '▼'}</span>
                      </button>
                      {isOpen && (
                        <div style={{ padding: '0.75rem 1rem', borderTop: '1px solid var(--color-border)', background: 'var(--color-card)' }}>
                          <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', marginBottom: '0.5rem', fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
                            <span><strong>Sannsynlighet:</strong> {risk.likelihood}</span>
                            <span><strong>Konsekvens:</strong> {risk.impact}</span>
                            <span><strong>Kategori:</strong> {riskMutation.data.category_labels[risk.category] ?? risk.category}</span>
                          </div>
                          {risk.reason && (
                            <div className="alert alert-info" style={{ marginBottom: '0.5rem', fontSize: '0.85rem' }}>
                              Relevant for ditt scenario: {risk.reason}
                            </div>
                          )}
                          <p style={{ fontSize: '0.9rem' }}><strong>Tiltak:</strong> {risk.mitigation}</p>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>

              <hr className="section-divider" />

              <h2>Komplett risikomatrise</h2>
              <table>
                <thead>
                  <tr><th>Risiko</th><th>Kategori</th><th>Sannsynlighet</th><th>Konsekvens</th><th>Samlet</th></tr>
                </thead>
                <tbody>
                  {riskMutation.data.assessed_risks.map(r => (
                    <tr key={r.name}>
                      <td>{r.name}</td>
                      <td>{riskMutation.data.category_labels[r.category] ?? r.category}</td>
                      <td>{r.likelihood}</td>
                      <td>{r.impact}</td>
                      <td style={{ color: SEVERITY_COLORS[r.overall] ?? '#333', fontWeight: 600 }}>{r.overall}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <hr className="section-divider" />

              <h2>Kritiske kontrollpunkter (HACCP)</h2>
              <p className="caption">
                For systemer beregnet på offentlig bruk kreves en formell HACCP-tilnærming, i henhold til norsk Vannforskrift.
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', margin: '1rem 0' }}>
                {riskMutation.data.ccps.map(ccp => {
                  const isOpen = openCcp === ccp.id
                  return (
                    <div key={ccp.id} style={{ border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
                      <button
                        onClick={() => setOpenCcp(isOpen ? null : ccp.id)}
                        style={{
                          width: '100%', textAlign: 'left', padding: '0.75rem 1rem',
                          background: 'var(--color-surface)', border: 'none', cursor: 'pointer',
                          display: 'flex', alignItems: 'center', gap: '0.5rem',
                          fontFamily: 'var(--font-body)',
                        }}
                      >
                        <span style={{ fontWeight: 600, color: 'var(--color-primary)' }}>{ccp.id}</span>
                        <span style={{ fontWeight: 500 }}>{ccp.name}</span>
                        <span style={{ marginLeft: 'auto', color: 'var(--color-text-muted)' }}>{isOpen ? '▲' : '▼'}</span>
                      </button>
                      {isOpen && (
                        <div style={{ padding: '0.75rem 1rem', borderTop: '1px solid var(--color-border)', background: 'var(--color-card)' }}>
                          <p style={{ margin: '0 0 0.4rem', fontSize: '0.9rem' }}><strong>Beskrivelse:</strong> {ccp.description}</p>
                          <p style={{ margin: 0, fontSize: '0.9rem' }}><strong>Kontrollmål:</strong> {ccp.control_measure}</p>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>

              <hr className="section-divider" />

              <h2>Bergen-spesifikke risikoer</h2>
              <div className="grid-2">
                <div>
                  <h3 style={{ fontSize: '1rem', margin: '0 0 0.5rem' }}>Eldre bygningsstock</h3>
                  <p className="caption" style={{ lineHeight: 1.6 }}>
                    Bergen har en betydelig andel pre-1970 trehus med blybeslag og blylodde renner, gamle malte
                    overflater med blybasert maling, og noe asbestsement-taktekning. En bygningsvis kartlegging
                    anbefales før implementering av nabolags- eller større systemer.
                  </p>
                </div>
                <div>
                  <h3 style={{ fontSize: '1rem', margin: '0 0 0.5rem' }}>Kyst- og bymiljø</h3>
                  <p className="caption" style={{ lineHeight: 1.6 }}>
                    Nærhet til sjøen introduserer marin aerosol (saltavsetning på tak), måseforurensning
                    (Campylobacter- og Salmonella-risiko), og tungmetaller fra historisk industriell
                    virksomhet i Laksevåg, Dokken og Nøstet.
                  </p>
                </div>
              </div>
            </>
          )}
        </>
      )}

      {/* ══════════════════════════════════════════════════════════════════════
          TAB: KOSTNADSANALYSE
         ══════════════════════════════════════════════════════════════════════ */}
      {tab === 'kostnader' && (
        <>
          <p className="subtitle" style={{ marginBottom: '1rem' }}>
            Indikative kostnadsestimater basert på systemtype og størrelse, med livsløpskostnader over 10–30 år.
          </p>

          {costsQuery.isPending && <p>Henter kostnadsdata…</p>}

          {costs && (
            <>
              <h2>Kostnadsestimat</h2>
              <p className="caption">
                Systemtype: <strong>{costs.estimate_label}</strong> for <strong>{fmt(population)} personer</strong>.
                Kostnadene er indikative og avhenger av lokale forhold, takets tilstand og valgt behandlingsnivå.
              </p>

              <div className="grid-3">
                <MetricCard
                  label="Investeringskostnad"
                  value={`${fmt(costs.capital)} kr`}
                  help={`Spenn: ${fmt(costs.capital_low)} – ${fmt(costs.capital_high)} kr`}
                  highlighted
                />
                <MetricCard
                  label="Årlig drift"
                  value={`${fmt(costs.annual_op)} kr/år`}
                  help={`Spenn: ${fmt(costs.annual_op_low)} – ${fmt(costs.annual_op_high)} kr`}
                />
                <MetricCard
                  label="Kostnad per person"
                  value={`${fmt(costs.cost_per_person)} kr`}
                />
              </div>

              <hr className="section-divider" />

              <h2>Livsløpskostnad</h2>
              <p className="caption">Total kostnad (investering + akkumulert drift) over tid. Godt designede systemer har en levetid på 20–40 år.</p>
              <ResponsiveContainer width="100%" height={260}>
                <AreaChart data={lifecycleData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#DCE3E9" />
                  <XAxis dataKey="år" tick={{ fontSize: 11 }} unit=" år" />
                  <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${fmt(v / 1000)}k`} />
                  <Tooltip
                    formatter={(v) => [`${fmt(Number(v))} kr`, 'Akkumulert kostnad']}
                    labelFormatter={l => `År ${l}`}
                  />
                  <Area type="monotone" dataKey="kostnad" stroke="#2B7A8E" fill="#2B7A8E" fillOpacity={0.35} dot={false} />
                </AreaChart>
              </ResponsiveContainer>

              <div className="grid-3" style={{ marginTop: '1rem' }}>
                <MetricCard label="10 år" value={`${fmt(costs.lifecycle_10)} kr`} />
                <MetricCard label="20 år" value={`${fmt(costs.lifecycle_20)} kr`} highlighted />
                <MetricCard label="30 år" value={`${fmt(costs.lifecycle_30)} kr`} />
              </div>

              {costs.cost_per_liter_20 != null && (
                <p style={{ marginTop: '0.75rem' }}>
                  Kostnad per liter (20 år): <strong>{costs.cost_per_liter_20.toFixed(2)} kr/L</strong>
                  <span className="caption"> — livsløpskostnad over 20 år delt på totalt oppsamlet vann.</span>
                </p>
              )}

              <hr className="section-divider" />

              <h2>Kostnadsfordeling</h2>
              <div className="grid-2">
                <div>
                  <h3 style={{ fontSize: '1rem', margin: '0 0 0.5rem' }}>Investering</h3>
                  <table>
                    <thead><tr><th>Kategori</th><th>Beløp (kr)</th></tr></thead>
                    <tbody>
                      {costs.capital_breakdown.map(row => (
                        <tr key={row.category}><td>{row.category}</td><td>{fmt(row.amount)}</td></tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div>
                  <h3 style={{ fontSize: '1rem', margin: '0 0 0.5rem' }}>Årlig drift</h3>
                  <table>
                    <thead><tr><th>Kategori</th><th>Beløp (kr)</th></tr></thead>
                    <tbody>
                      {costs.operating_breakdown.map(row => (
                        <tr key={row.category}><td>{row.category}</td><td>{fmt(row.amount)}</td></tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <hr className="section-divider" />

              <h2>Kostnadsoversikt per systemtype</h2>
              <table>
                <thead>
                  <tr><th>Systemtype</th><th>Inv. lav</th><th>Inv. høy</th><th>Drift lav</th><th>Drift høy</th><th>Kapasitet</th></tr>
                </thead>
                <tbody>
                  {costs.all_estimates.map(e => (
                    <tr key={e.label} style={{ background: e.label === costs.estimate_label ? 'var(--color-primary-light)' : undefined }}>
                      <td><strong>{e.label === costs.estimate_label ? e.label + ' ✓' : e.label}</strong></td>
                      <td>{fmt(e.capital_low)}</td>
                      <td>{fmt(e.capital_high)}</td>
                      <td>{fmt(e.annual_operating_low)}</td>
                      <td>{fmt(e.annual_operating_high)}</td>
                      <td>{e.capacity_low}–{e.capacity_high}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <hr className="section-divider" />

              <h2>Nyttevurdering for offentlig investering</h2>
              <ul style={{ lineHeight: 1.8, paddingLeft: '1.2rem' }}>
                <li><strong>Unngåtte krisekostnader</strong> — kostnadene ved nød-vannforsyning med flaskevann og tankbiler er svært høye. Ett unngått hendelse kan forsvare investeringen.</li>
                <li><strong>Folkehelsebeskyttelse</strong> — opprettholdelse av drikkevannstilgang under kriser forebygger vannbårne sykdommer.</li>
                <li><strong>Forsikringsverdi</strong> — lavere sannsynlighet for forsyningssvikt reduserer kommunalt ansvar og forsikringsrisiko.</li>
                <li><strong>Dobbeltbruksdividende</strong> — systemer med normalbruk (toalettspyling, vanning) kompenserer driftskostnader gjennom redusert kommunalt vannforbruk.</li>
                <li><strong>Klimatilpasning</strong> — investeringen teller mot Bergens klimatilpasningsforpliktelser under Klimaplan for Bergen 2030.</li>
                <li><strong>Lang levetid</strong> — godt designede systemer har 20–40 års operasjonell levetid.</li>
              </ul>
            </>
          )}
        </>
      )}
    </div>
  )
}
