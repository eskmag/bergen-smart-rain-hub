import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, keepPreviousData } from '@tanstack/react-query'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import { api } from '../api/client'
import LandingNav from '../components/LandingNav'
import Kjelder from '../components/shared/Kjelder'
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
  const { data: validation } = useQuery({ queryKey: ['validation'], queryFn: api.validation })

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
            Hva om <strong>hvert femte tak</strong><br />
            i Bergen samlet regnvann?
          </h1>
          <p className="l-hero-sub">
            Bydel for bydel: hvor mange mennesker kan få dekket WHOs
            overlevelsesminimum fra takflatene som allerede finnes — uten nye bygg,
            bare oppsamling fra en del av dem.
          </p>
          <div className="l-hero-actions">
            <button
              className="l-btn-ghost"
              onClick={() => document.getElementById('metode')?.scrollIntoView({ behavior: 'smooth' })}
            >
              Slik regner vi
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
              Mennesker dekket til WHO-minimum · {participation} % deltakelse
            </div>
          </div>
          <div className="l-hero-stat-grid">
            <div className="l-hsg-item">
              <div className="l-hsg-num">{data ? `${fmt(data.demand_coverage_pct, 1)} %` : '—'}</div>
              <div className="l-hsg-label">Av hele byens minimumsbehov</div>
            </div>
            <div className="l-hsg-item">
              <div className="l-hsg-num">
                {data ? `${fmt(data.total_daily_liters / 1_000_000, 1)} mill. L` : '—'}
              </div>
              <div className="l-hsg-label">Oppsamlet per dag i snitt</div>
            </div>
            <div className="l-hsg-item">
              <div className="l-hsg-num">{data ? data.bydeler.length : '—'}</div>
              <div className="l-hsg-label">Bydeler analysert</div>
            </div>
            <div className="l-hsg-item">
              <div className="l-hsg-num">{totalPopulation ? fmt(totalPopulation) : '—'}</div>
              <div className="l-hsg-label">Innbyggere totalt</div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Slider strip ── */}
      <section className="p-slider-strip">
        <div className="p-slider-copy">
          <div className="p-slider-title">Deltakelsesgrad: hvor mange tak blir med?</div>
          <div className="p-slider-hint">
            Deltakelse = andelen av det egnede takarealet som faktisk blir koblet til
            oppsamling. 20 % svarer omtrent til hvert femte tak i byen.
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
            aria-label="Deltakelsesgrad i prosent"
          />
          <span className="p-slider-value">{participation} %</span>
        </label>
      </section>

      {/* ── Method narrative ── */}
      <section className="l-narrative" id="metode">
        <p className="l-section-eyebrow">Slik regner vi</p>
        <div className="l-narrative-steps">
          <div className="l-narrative-step">
            <div className="l-step-index">01</div>
            <h3 className="l-step-title">Takareal per bydel</h3>
            <p className="l-step-body">
              Hver innbygger regnes å ha {data ? fmt(data.roof_m2_per_capita) : '—'} m²
              egnet takflate — et konservativt anslag. Tette bydeler som Bergenhus og
              Årstad får en reduksjonsfaktor, siden blokker deler tak på flere.
              Deltakelsesgraden avgjør hvor mye av dette som faktisk blir koblet til.
            </p>
          </div>
          <div className="l-narrative-step">
            <div className="l-step-index">02</div>
            <h3 className="l-step-title">Nedbør blir til vann</h3>
            <p className="l-step-body">
              Normalnedbøren i Bergen er {rainfallMm ? fmt(rainfallMm) : '—'} mm i året —
              én millimeter regn gir én liter per kvadratmeter tak. Med{' '}
              {efficiencyPct ?? '—'} % systemvirkningsgrad blir det gjennomsnittlig
              daglig oppsamling per bydel.
            </p>
          </div>
          <div className="l-narrative-step">
            <div className="l-step-index">03</div>
            <h3 className="l-step-title">Målt mot krisebehovet</h3>
            <p className="l-step-body">
              WHOs overlevelsesminimum er {whoLiters ?? '—'} liter per person per dag.
              Oppsamlingen delt på behovet gir dekningsgraden — og fordi takene samler mer
              enn minimumsbehovet, kan dekningen passere 100 %. Det er ikke en feil,
              det er margin.
            </p>
          </div>
        </div>

        {validation && validation.longest_dry_spell.days > 0 && (
          <div className="p-validering">
            <span className="p-validering-tag">Validert mot virkeligheten</span>
            <p className="p-validering-body">
              Modellen kjenner igjen tørkeperioden mai–juni 2018
              ({validation.longest_dry_spell.days} dager,{' '}
              {validation.longest_dry_spell.start}–{validation.longest_dry_spell.end})
              fra faktiske MET-målinger ved Bergen Florida.
            </p>
          </div>
        )}
      </section>

      {/* ── Results ── */}
      <section className="p-results">
        <p className="l-section-eyebrow">Resultat per bydel</p>
        <div className="p-results-grid">
          <div className="p-chart-card">
            <h2 className="p-card-title">Dekningsgrad ved {participation} % deltakelse</h2>
            <p className="p-card-note">
              Tette bydeler har mindre takareal per innbygger — derfor ligger Bergenhus lavest.
            </p>
            {isLoading || !data ? (
              <p className="p-placeholder">Beregner…</p>
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
              <h2 className="p-card-title">Tallene bak søylene</h2>
              <div className="p-table-scroll">
                <table className="p-table">
                  <thead>
                    <tr>
                      <th>Bydel</th>
                      <th className="p-num">Innbyggere</th>
                      <th className="p-num">Egnet takareal (m²)</th>
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
                      <td>Hele Bergen</td>
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
          <p className="l-section-eyebrow">Forutsetninger</p>
          <h2 className="l-data-title">Grove tall, ærlig presentert.</h2>
          <p className="l-data-body">
            Takarealene er førsteordens estimater: folketall ganger et antatt egnet areal per
            innbygger. Det er en dokumentert antakelse — ikke målte tak. Neste steg er å
            erstatte anslaget med reelle bygningsfotavtrykk fra Kartverket (FKB-bygning).
            Frem til da bør tallene leses som størrelsesordener: de viser at potensialet er
            reelt og stort, ikke nøyaktig hvor stort.
          </p>
        </div>
        <div className="l-data-facts">
          <div className="l-data-fact">
            <div className="l-df-num">{data ? `${fmt(data.roof_m2_per_capita)} m²` : '—'}</div>
            <div className="l-df-label">Antatt egnet takareal per innbygger (redusert i tette bydeler)</div>
          </div>
          <div className="l-data-fact">
            <div className="l-df-num">{rainfallMm ? `${fmt(rainfallMm)} mm` : '—'}</div>
            <div className="l-df-label">Normalnedbør per år, jevnt fordelt (årsgjennomsnitt)</div>
          </div>
          <div className="l-data-fact">
            <div className="l-df-num">{efficiencyPct ? `${efficiencyPct} %` : '—'}</div>
            <div className="l-df-label">Systemvirkningsgrad — realistisk, ikke optimistisk</div>
          </div>
          <div className="l-data-fact">
            <div className="l-df-num">{whoLiters ? `${whoLiters} L` : '—'}</div>
            <div className="l-df-label">WHO overlevelsesminimum per person per dag</div>
          </div>
        </div>
      </section>

      {/* ── CTA + footer ── */}
      <section className="l-cta-section">
        <div className="l-cta-left">
          <p className="l-cta-eyebrow">Fra by til bygg</p>
          <h2 className="l-cta-title">Hva betyr dette for ditt bygg?</h2>
          <p className="l-cta-sub">Kalkulatoren simulerer tanknivå dag for dag med ekte nedbørsdata</p>
        </div>
        <div className="l-cta-right">
          <Link to="/beregn" className="l-cta-btn">
            <svg className="l-icon" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M9 7H6a2 2 0 00-2 2v9a2 2 0 002 2h9a2 2 0 002-2v-3M13 3h8m0 0v8m0-8L11 13" />
            </svg>
            Beregn ditt bygg
          </Link>
          <p className="l-cta-note">Ekte nedbørsdata fra MET · WHO-standarder</p>
        </div>
      </section>
      <footer className="l-footer">
        <span className="l-footer-left">
          © 2026 Bergen Smart Rain Hub · Folketall: SSB / Bergen kommune bydelsfakta (2024)
        </span>
        <ul className="l-footer-links">
          <li><Link to="/">Forsiden</Link></li>
          <li><a href="/#data">Datakilde</a></li>
        </ul>
      </footer>
      <div className="l-footer-kjelder">
        <Kjelder ids={['who', 'met', 'normal', 'dsb', 'framework']} />
      </div>
    </div>
  )
}
