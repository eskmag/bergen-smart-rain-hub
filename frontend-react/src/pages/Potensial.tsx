import { useState } from 'react'
import { useQuery, keepPreviousData } from '@tanstack/react-query'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import { api } from '../api/client'
import LandingNav from '../components/LandingNav'
import '../landing.css'
import '../potensial.css'

function fmt(n: number) {
  return n.toLocaleString('nb-NO')
}

export default function Potensial() {
  // Participation in whole percent for the slider; API takes a fraction.
  const [participation, setParticipation] = useState(20)

  const { data, isLoading } = useQuery({
    queryKey: ['bydel', participation],
    queryFn: () => api.bydel(participation / 100),
    placeholderData: keepPreviousData,
  })

  return (
    <div className="l-shell">
      <LandingNav />

      <section className="p-hero">
        <p className="l-section-eyebrow">Policy-visning</p>
        <h1 className="p-title">Hvor mye av Bergens nødvannbehov kan takene dekke?</h1>
        <p className="p-sub">
          Aggregert potensial per bydel: gjennomsnittlig daglig oppsamling fra egnede
          takflater målt mot WHO sitt overlevelsesminimum for hele befolkningen.
        </p>

        <div className="p-headline-card">
          <div className="p-headline-num">
            {data ? `${data.demand_coverage_pct.toLocaleString('nb-NO')} %` : '…'}
          </div>
          <div className="p-headline-label">
            av Bergens nødvannbehov dekket ved {participation} % deltakelse
          </div>
        </div>

        <label className="p-slider-row">
          <span className="p-slider-label">Deltakelsesgrad</span>
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
        <p className="p-slider-hint">
          Andel av det egnede takarealet som faktisk kobles til oppsamling.
        </p>
      </section>

      <section className="p-content">
        <div className="p-chart-card">
          <h2 className="p-card-title">Dekningsgrad per bydel</h2>
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
                <YAxis
                  type="category"
                  dataKey="label"
                  tick={{ fontSize: 12 }}
                  width={96}
                />
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
            <h2 className="p-card-title">Tall per bydel</h2>
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
                      <td className="p-num">{row.coverage_pct.toLocaleString('nb-NO')} %</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr>
                    <td>Hele Bergen</td>
                    <td className="p-num"></td>
                    <td className="p-num"></td>
                    <td className="p-num">{fmt(data.total_daily_liters)}</td>
                    <td className="p-num">{fmt(data.total_demand_liters)}</td>
                    <td className="p-num">{data.demand_coverage_pct.toLocaleString('nb-NO')} %</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        )}

        {data && (
          <details className="p-assumptions">
            <summary>Forutsetninger</summary>
            <ul>
              {data.assumptions.map((a) => (
                <li key={a}>{a}</li>
              ))}
            </ul>
            <p className="p-assumptions-note">
              Takarealene er førsteordens estimater (befolkning × antatt egnet areal per
              innbygger). Forbedring med FKB-bygningsdata fra Kartverket er planlagt arbeid.
            </p>
          </details>
        )}
      </section>
    </div>
  )
}
