import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  AreaChart, Area, XAxis, YAxis,
  CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer,
} from 'recharts'
import { api } from '../api/client'
import { useBeredskap } from '../context/BeredskapsContext'
import { MetricCard } from '../components/MetricCard'

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

function verdictFor(supplyDays: number) {
  if (supplyDays >= 14) return { text: 'Godt potensial', color: '#1a7f4e', bg: '#d1e7dd' }
  if (supplyDays >= 7)  return { text: 'Tilstrekkelig',  color: '#b07a12', bg: '#fff3cd' }
  return                       { text: 'Kritisk',        color: '#842029', bg: '#f8d7da' }
}

export default function Beregn() {
  const {
    numBuildings, setNumBuildings,
    population, setPopulation,
    scale,
    setRoofPerBuilding,
    setScale,
    setHeightM,
    simResult, isSimPending,
    riskResult,
    annualLiters,
  } = useBeredskap()

  const { data: config } = useQuery({ queryKey: ['config'], queryFn: api.config })

  const costsQuery = useQuery({
    queryKey: ['costs', population, scale, Math.round(annualLiters)],
    queryFn: () => api.costs(population, scale, annualLiters),
    enabled: population > 0 && annualLiters > 0,
  })

  const [selectedKey, setSelectedKey] = useState<BuildingKey>('enebolig')
  const [simOpen, setSimOpen] = useState(false)
  const [riskOpen, setRiskOpen] = useState(false)
  const [costsOpen, setCostsOpen] = useState(false)

  const selectedOption = BUILDING_OPTIONS.find(o => o.key === selectedKey)!
  const isNeighbourhood = selectedOption.scale === 'neighbourhood'

  function handleBuildingSelect(key: BuildingKey) {
    const preset = config?.building_presets.find(p => p.key === key)
    const opt = BUILDING_OPTIONS.find(o => o.key === key)!
    setSelectedKey(key)
    if (preset) {
      setRoofPerBuilding(preset.roof_area_m2)
      setHeightM(preset.height_m)
      setPopulation(opt.scale === 'neighbourhood' ? preset.default_people * numBuildings : preset.default_people)
    }
    setScale(opt.scale)
    if (opt.scale === 'household') setNumBuildings(1)
  }

  const summary = simResult?.summary ?? {}
  const supplyDays    = (summary['days_of_survival_supply'] ?? 0) as number
  const totalLiters   = (summary['total_collected_liters'] ?? annualLiters) as number
  const daysTankEmpty = (summary['days_tank_empty'] ?? 0) as number
  const longestDry    = (summary['longest_dry_spell_days'] ?? 0) as number

  const verdict = verdictFor(supplyDays)

  const waterNeedPerDay = config?.water_needs?.['survival_total'] ?? 13
  const dailyNeed = population * waterNeedPerDay

  const tankOptions = [
    { label: 'Minimum',  liters: dailyNeed * 7,  desc: 'Klarer 7 dager uten regn' },
    { label: 'Anbefalt', liters: dailyNeed * 14, desc: 'Klarer 14 dager uten regn' },
    { label: 'Komfort',  liters: dailyNeed * 21, desc: 'Klarer 21 dager uten regn' },
  ]

  const baseLabel = config?.building_presets.find(p => p.key === selectedKey)?.label ?? selectedOption.label
  const displayLabel = isNeighbourhood && numBuildings > 1 ? `${numBuildings} × ${baseLabel}` : baseLabel

  const topRisks = (riskResult?.assessed_risks ?? []).slice(0, 3)
  const costs = costsQuery.data

  return (
    <div className="page-content">
      <h1>Beregn din beredskap</h1>
      <p className="subtitle">
        Velg bygningstype og antall personer — vi simulerer regnvannsoppsamling basert på 365 dager
        med historiske data fra Bergen og viser hvor lenge vannet rekker ved en krise.
      </p>

      <h2>Velg bygningstype</h2>
      <div className="building-grid">
        {BUILDING_OPTIONS.map(opt => (
          <button
            key={opt.key}
            className={`building-card${selectedKey === opt.key ? ' selected' : ''}`}
            onClick={() => handleBuildingSelect(opt.key)}
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
              <span className="slider-label-value">{numBuildings}</span>
            </div>
            <input
              type="range" min={2} max={20} step={1}
              value={numBuildings}
              onChange={e => {
                const n = Number(e.target.value)
                setNumBuildings(n)
                const preset = config?.building_presets.find(p => p.key === selectedKey)
                if (preset) setPopulation(preset.default_people * n)
              }}
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
            type="range" min={1} max={isNeighbourhood ? 5000 : 20} step={1}
            value={population}
            onChange={e => setPopulation(Number(e.target.value))}
          />
        </div>
      </div>

      {isSimPending && (
        <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem', marginTop: '1rem' }}>Simulerer…</p>
      )}

      {simResult && (
        <>
          {/* Verdict */}
          <div
            className="verdict-card"
            style={{ background: verdict.bg, borderColor: verdict.color, marginBottom: '1.5rem', marginTop: '1.5rem' }}
          >
            <h3 style={{ color: verdict.color, fontSize: '1.35rem', fontWeight: 800, margin: '0 0 0.5rem' }}>
              {verdict.text}
            </h3>
            <p style={{ margin: 0, fontSize: '1.05rem', lineHeight: 1.6 }}>
              {displayLabel} kan samle opp <strong>{fmt(totalLiters)} liter</strong> regnvann i året —
              nok til <strong>{fmt(population)} {population === 1 ? 'person' : 'personer'}</strong> i{' '}
              <strong>{fmt(supplyDays)} dager</strong> ved en krise.
            </p>
          </div>

          {/* Key metrics */}
          <div className="grid-4">
            <MetricCard label="Årlig oppsamling"   value={`${fmt(totalLiters)} L`} />
            <MetricCard label="Beredskapsforsyning" value={`${fmt(supplyDays)} dager`} highlighted />
            <MetricCard label="Dager tank tom"      value={`${fmt(daysTankEmpty)}`} />
            <MetricCard label="Lengste tørkeperiode" value={`${fmt(longestDry)} dager`} />
          </div>

          {/* Tank sizing */}
          <h2 style={{ marginTop: '1.5rem' }}>Anbefalt tankstørrelse</h2>
          <p className="caption">
            Velg størrelse ut fra hvor mange dager uten regn du vil være forberedt på.
            Bergen kan ha tørkeperioder på 3–4 uker.
          </p>
          <div className="metric-grid-3">
            {tankOptions.map(opt => (
              <div key={opt.label} className={`tank-card${opt.label === 'Anbefalt' ? ' recommended' : ''}`}>
                <div className="tank-card-label">{opt.label}</div>
                <div className="tank-card-value">{fmt(opt.liters)} L</div>
                <div className="tank-card-desc">{opt.desc}</div>
                <div className="tank-card-desc">= {(opt.liters / 1000).toFixed(1)} m³</div>
              </div>
            ))}
          </div>

          {/* Expandable: Simuleringsdetaljer */}
          <div className="disclosure-section">
            <button className="disclosure-header" onClick={() => setSimOpen(v => !v)}>
              <span>Simuleringsdetaljer</span>
              <span className={`disclosure-chevron${simOpen ? ' open' : ''}`}>▾</span>
            </button>
            {simOpen && (
              <div className="disclosure-body">
                <h3>Tanknivå gjennom året</h3>
                <p className="caption">
                  Regn fyller tanken, daglig forbruk tømmer den. Den røde linjen markerer kritisk nivå (20&nbsp;%).
                </p>
                <ResponsiveContainer width="100%" height={260}>
                  <AreaChart data={simResult.simulation_series} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#DCE3E9" />
                    <XAxis dataKey="date" tickFormatter={d => d.slice(5)} tick={{ fontSize: 11 }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
                    <Tooltip
                      formatter={v => [`${Number(v).toFixed(1)} %`, 'Tanknivå']}
                      labelFormatter={l => `Dato: ${l}`}
                    />
                    <ReferenceLine y={20} stroke="#C1292E" strokeDasharray="4 4" />
                    <Area
                      type="monotone" dataKey="tank_pct"
                      stroke="var(--color-primary)" fill="var(--color-primary)" fillOpacity={0.25} dot={false}
                    />
                  </AreaChart>
                </ResponsiveContainer>

                {simResult.dry_spells.length > 0 && (
                  <>
                    <h3 style={{ marginTop: '1.25rem' }}>Tørkeperioder</h3>
                    <table>
                      <thead>
                        <tr><th>Start</th><th>Slutt</th><th>Dager</th><th>Total nedbør (mm)</th></tr>
                      </thead>
                      <tbody>
                        {[...simResult.dry_spells]
                          .sort((a, b) => b.days - a.days)
                          .map((s, i) => (
                            <tr key={i}>
                              <td>{s.start}</td><td>{s.end}</td>
                              <td>{s.days}</td><td>{s.total_rain_mm.toFixed(1)}</td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </>
                )}

                <div style={{ marginTop: '1rem' }}>
                  <Link to="/beredskap" className="cta-link">Se full simulering →</Link>
                </div>
              </div>
            )}
          </div>

          {/* Expandable: Risikovurdering */}
          <div className="disclosure-section">
            <button className="disclosure-header" onClick={() => setRiskOpen(v => !v)}>
              <span>Risikovurdering</span>
              <span className={`disclosure-chevron${riskOpen ? ' open' : ''}`}>▾</span>
            </button>
            {riskOpen && (
              <div className="disclosure-body">
                {topRisks.length === 0 ? (
                  <p style={{ color: 'var(--color-text-muted)' }}>Risikovurdering beregnes…</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {topRisks.map((risk, i) => {
                      const isHigh = risk.overall === 'Høy'
                      const isMed  = risk.overall === 'Middels'
                      return (
                        <div key={i} style={{
                          background: 'var(--color-surface)',
                          border: '1px solid var(--color-border)',
                          borderRadius: 'var(--radius-sm)',
                          padding: '0.75rem 1rem',
                          display: 'flex', gap: '0.75rem', alignItems: 'flex-start',
                        }}>
                          <span style={{
                            padding: '0.15rem 0.5rem',
                            borderRadius: 'var(--radius-pill)',
                            fontSize: '0.75rem', fontWeight: 700, flexShrink: 0,
                            background: isHigh ? '#f8d7da' : isMed ? '#fff3cd' : '#d1e7dd',
                            color:      isHigh ? '#842029' : isMed ? '#664d03' : '#0f5132',
                          }}>
                            {risk.overall}
                          </span>
                          <div>
                            <div style={{ fontWeight: 600 }}>{risk.name}</div>
                            <div style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
                              {risk.mitigation}
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
                <div style={{ marginTop: '1rem' }}>
                  <Link to="/beredskap/risiko" className="cta-link">Se full risikovurdering →</Link>
                </div>
              </div>
            )}
          </div>

          {/* Expandable: Kostnadsoverslag */}
          <div className="disclosure-section">
            <button className="disclosure-header" onClick={() => setCostsOpen(v => !v)}>
              <span>Hva koster det?</span>
              <span className={`disclosure-chevron${costsOpen ? ' open' : ''}`}>▾</span>
            </button>
            {costsOpen && (
              <div className="disclosure-body">
                {!costs ? (
                  <p style={{ color: 'var(--color-text-muted)' }}>Henter kostnadsdata…</p>
                ) : (
                  <>
                    <p className="caption">
                      Systemtype: <strong>{costs.estimate_label}</strong> — indikative kostnader for{' '}
                      <strong>{fmt(population)} {population === 1 ? 'person' : 'personer'}</strong>.
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
                  </>
                )}
                <div style={{ marginTop: '1rem' }}>
                  <Link to="/beredskap/kostnader" className="cta-link">Se full kostnadsanalyse →</Link>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
