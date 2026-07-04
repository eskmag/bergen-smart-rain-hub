import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, keepPreviousData } from '@tanstack/react-query'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import { api } from '../api/client'
import LandingNav from '../components/LandingNav'
import '../landing.css'
import '../potensial.css'

function fmt(n: number, decimals = 0) {
  return n.toLocaleString('nb-NO', { maximumFractionDigits: decimals })
}

export default function Potensial() {
  // Participation in whole percent for the slider; API takes a fraction.
  const [participation, setParticipation] = useState(20)

  const { data, isLoading } = useQuery({
    queryKey: ['bydel', participation],
    queryFn: () => api.bydel(participation / 100),
    placeholderData: keepPreviousData,
  })
  const { data: config } = useQuery({ queryKey: ['config'], queryFn: api.config })

  const efficiencyPct = config ? Math.round(config.defaults.collection_efficiency * 100) : null
  const rainfallMm = config ? Math.round(config.defaults.annual_rainfall_mm) : null
  const whoLiters = config ? Math.round(config.water_needs.survival_total) : null
  const totalPopulation = data
    ? data.bydeler.reduce((s, b) => s + b.population, 0)
    : null

  return (
    <div className="l-shell">
      <LandingNav />

      {/* ── Hero ── */}
      <section className="l-hero">
        <div>
          <p className="l-eyebrow">Policy-visning · Kommune og beredskap</p>
          <h1 className="l-hero-title">
            Kva om <strong>kvart femte tak</strong><br />
            i Bergen samla regnvatn?
          </h1>
          <p className="l-hero-sub">
            Bydel for bydel: kor mange menneske kan få dekt WHO sitt
            overlevingsminimum frå takflatene som allereie finst — utan nye bygg,
            berre oppsamling frå ein del av dei.
          </p>
          <div className="l-hero-actions">
            <button
              className="l-btn-ghost"
              onClick={() => document.getElementById('metode')?.scrollIntoView({ behavior: 'smooth' })}
            >
              Slik reknar vi
              <svg className="l-icon-sm" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </div>
        </div>
        <div className="l-hero-right">
          <div className="l-hero-stat-main">
            <div className="l-hsm-num">{data ? `≈ ${fmt(data.persons_covered)}` : '—'}</div>
            <div className="l-hsm-label">
              Menneske dekt til WHO-minimum · {participation} % deltaking
            </div>
          </div>
          <div className="l-hero-stat-grid">
            <div className="l-hsg-item">
              <div className="l-hsg-num">{data ? `${fmt(data.demand_coverage_pct, 1)} %` : '—'}</div>
              <div className="l-hsg-label">Av heile byens minimumsbehov</div>
            </div>
            <div className="l-hsg-item">
              <div className="l-hsg-num">
                {data ? `${fmt(data.total_daily_liters / 1_000_000, 1)} mill. L` : '—'}
              </div>
              <div className="l-hsg-label">Oppsamla per dag i snitt</div>
            </div>
            <div className="l-hsg-item">
              <div className="l-hsg-num">{data ? data.bydeler.length : '—'}</div>
              <div className="l-hsg-label">Bydelar analysert</div>
            </div>
            <div className="l-hsg-item">
              <div className="l-hsg-num">{totalPopulation ? fmt(totalPopulation) : '—'}</div>
              <div className="l-hsg-label">Innbyggarar totalt</div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Slider strip ── */}
      <section className="p-slider-strip">
        <div className="p-slider-copy">
          <div className="p-slider-title">Deltakingsgrad: kor mange tak blir med?</div>
          <div className="p-slider-hint">
            Deltaking = delen av det egna takarealet som faktisk blir kopla til
            oppsamling. 20 % svarar omtrent til kvart femte tak i byen.
          </div>
        </div>
        <label className="p-slider-control">
          <input
            type="range"
            min={10}
            max={100}
            step={5}
            value={participation}
            onChange={(e) => setParticipation(Number(e.target.value))}
            aria-label="Deltakingsgrad i prosent"
          />
          <span className="p-slider-value">{participation} %</span>
        </label>
      </section>

      {/* ── Method narrative ── */}
      <section className="l-narrative" id="metode">
        <p className="l-section-eyebrow">Slik reknar vi</p>
        <div className="l-narrative-steps">
          <div className="l-narrative-step">
            <div className="l-step-index">01</div>
            <h3 className="l-step-title">Takareal per bydel</h3>
            <p className="l-step-body">
              Kvar innbyggar reknast å ha {data ? fmt(data.roof_m2_per_capita) : '—'} m²
              egna takflate — eit konservativt anslag. Tette bydelar som Bergenhus og
              Årstad får ein reduksjonsfaktor, sidan blokker deler tak på fleire.
              Deltakingsgraden avgjer kor mykje av dette som faktisk blir kopla til.
            </p>
          </div>
          <div className="l-narrative-step">
            <div className="l-step-index">02</div>
            <h3 className="l-step-title">Nedbør blir til vatn</h3>
            <p className="l-step-body">
              Normalnedbøren i Bergen er {rainfallMm ? fmt(rainfallMm) : '—'} mm i året —
              éin millimeter regn gir éin liter per kvadratmeter tak. Med{' '}
              {efficiencyPct ?? '—'} % systemvirkningsgrad blir det gjennomsnittleg
              daglig oppsamling per bydel.
            </p>
          </div>
          <div className="l-narrative-step">
            <div className="l-step-index">03</div>
            <h3 className="l-step-title">Målt mot krisebehovet</h3>
            <p className="l-step-body">
              WHO sitt overlevingsminimum er {whoLiters ?? '—'} liter per person per dag.
              Oppsamlinga delt på behovet gir dekningsgraden — og fordi taka samlar meir
              enn minimumsbehovet, kan dekninga passere 100 %. Det er ikkje ein feil,
              det er margin.
            </p>
          </div>
        </div>
      </section>

      {/* ── Results ── */}
      <section className="p-results">
        <p className="l-section-eyebrow">Resultat per bydel</p>
        <div className="p-results-grid">
          <div className="p-chart-card">
            <h2 className="p-card-title">Dekningsgrad ved {participation} % deltaking</h2>
            <p className="p-card-note">
              Tette bydelar har mindre takareal per innbyggar — difor ligg Bergenhus lågast.
            </p>
            {isLoading || !data ? (
              <p className="p-placeholder">Bereknar…</p>
            ) : (
              <ResponsiveContainer width="100%" height={320}>
                <BarChart
                  data={data.bydeler}
                  layout="vertical"
                  margin={{ top: 5, right: 40, left: 24, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#EDF0F3" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 11 }} unit=" %" />
                  <YAxis type="category" dataKey="label" tick={{ fontSize: 12 }} width={96} />
                  <Tooltip
                    formatter={(v) => [`${Number(v).toLocaleString('nb-NO')} %`, 'Dekning']}
                  />
                  <Bar
                    dataKey="coverage_pct"
                    fill="var(--color-primary)"
                    radius={[0, 3, 3, 0]}
                    barSize={18}
                  />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          {data && (
            <div className="p-table-card">
              <h2 className="p-card-title">Tala bak søylene</h2>
              <div className="p-table-scroll">
                <table className="p-table">
                  <thead>
                    <tr>
                      <th>Bydel</th>
                      <th className="p-num">Innbyggarar</th>
                      <th className="p-num">Egna takareal (m²)</th>
                      <th className="p-num">Oppsamling (L/dag)</th>
                      <th className="p-num">Behov (L/dag)</th>
                      <th className="p-num">Dekning</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.bydeler.map((row) => (
                      <tr key={row.key}>
                        <td>{row.label}</td>
                        <td className="p-num">{fmt(row.population)}</td>
                        <td className="p-num">{fmt(row.suitable_roof_m2)}</td>
                        <td className="p-num">{fmt(row.daily_yield_liters)}</td>
                        <td className="p-num">{fmt(row.demand_liters)}</td>
                        <td className="p-num">{fmt(row.coverage_pct, 1)} %</td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr>
                      <td>Heile Bergen</td>
                      <td className="p-num">{totalPopulation ? fmt(totalPopulation) : ''}</td>
                      <td className="p-num"></td>
                      <td className="p-num">{fmt(data.total_daily_liters)}</td>
                      <td className="p-num">{fmt(data.total_demand_liters)}</td>
                      <td className="p-num">{fmt(data.demand_coverage_pct, 1)} %</td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* ── Assumptions / data quality ── */}
      <section className="l-data-section">
        <div>
          <p className="l-section-eyebrow">Forutsetningar</p>
          <h2 className="l-data-title">Grove tal, ærleg presenterte.</h2>
          <p className="l-data-body">
            Takareala er førsteordens estimat: folketal gonger eit antatt egna areal per
            innbyggar. Det er ein dokumentert antaking — ikkje målte tak. Neste steg er å
            erstatte anslaget med reelle bygningsfotavtrykk frå Kartverket (FKB-bygning).
            Fram til då bør tala lesast som storleiksordenar: dei viser at potensialet er
            reelt og stort, ikkje nøyaktig kor stort.
          </p>
        </div>
        <div className="l-data-facts">
          <div className="l-data-fact">
            <div className="l-df-num">{data ? `${fmt(data.roof_m2_per_capita)} m²` : '—'}</div>
            <div className="l-df-label">Antatt egna takareal per innbyggar (redusert i tette bydelar)</div>
          </div>
          <div className="l-data-fact">
            <div className="l-df-num">{rainfallMm ? `${fmt(rainfallMm)} mm` : '—'}</div>
            <div className="l-df-label">Normalnedbør per år, jamt fordelt (årsgjennomsnitt)</div>
          </div>
          <div className="l-data-fact">
            <div className="l-df-num">{efficiencyPct ? `${efficiencyPct} %` : '—'}</div>
            <div className="l-df-label">Systemvirkningsgrad — realistisk, ikkje optimistisk</div>
          </div>
          <div className="l-data-fact">
            <div className="l-df-num">{whoLiters ? `${whoLiters} L` : '—'}</div>
            <div className="l-df-label">WHO overlevingsminimum per person per dag</div>
          </div>
        </div>
      </section>

      {/* ── CTA + footer ── */}
      <section className="l-cta-section">
        <div className="l-cta-left">
          <p className="l-cta-eyebrow">Frå by til bygg</p>
          <h2 className="l-cta-title">Kva betyr dette for ditt bygg?</h2>
          <p className="l-cta-sub">Kalkulatoren simulerer tanknivå dag for dag med ekte nedbørsdata</p>
        </div>
        <div className="l-cta-right">
          <Link to="/beregn" className="l-cta-btn">
            <svg className="l-icon" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M9 7H6a2 2 0 00-2 2v9a2 2 0 002 2h9a2 2 0 002-2v-3M13 3h8m0 0v8m0-8L11 13" />
            </svg>
            Beregn ditt bygg
          </Link>
          <p className="l-cta-note">Ekte nedbørsdata frå MET · WHO-standardar</p>
        </div>
      </section>
      <footer className="l-footer">
        <span className="l-footer-left">
          © 2026 Bergen Smart Rain Hub · Folketal: SSB / Bergen kommune bydelsfakta (2024)
        </span>
        <ul className="l-footer-links">
          <li><Link to="/">Framsida</Link></li>
          <li><a href="/#data">Datakjelde</a></li>
        </ul>
      </footer>
    </div>
  )
}
