import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  AreaChart, Area, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import { api } from '../api/client'
import { MetricCard } from '../components/MetricCard'
import { useBeredskap } from '../context/BeredskapsContext'

function fmt(n: number, decimals = 0) {
  return n.toLocaleString('nb-NO', { maximumFractionDigits: decimals })
}

export default function Kostnader() {
  const { population, scale, annualLiters } = useBeredskap()

  const costsQuery = useQuery({
    queryKey: ['costs', population, scale, Math.round(annualLiters)],
    queryFn: () => api.costs(population, scale, annualLiters),
    enabled: population > 0,
  })

  const costs = costsQuery.data

  const lifecycleData = useMemo(() => {
    if (!costs) return []
    return Array.from({ length: 31 }, (_, y) => ({
      år: y,
      kostnad: costs.capital + costs.annual_op * y,
    }))
  }, [costs])

  if (costsQuery.isPending) {
    return <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>Henter kostnadsdata…</p>
  }

  if (!costs) return null

  return (
    <>
      <p className="subtitle" style={{ marginBottom: '1rem' }}>
        Indikative kostnadsestimater basert på systemtype og størrelse, med livsløpskostnader over 10–30 år.
      </p>

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
          <Area type="monotone" dataKey="kostnad" stroke="#2B7A8E" fill="#2B7A8E" fillOpacity={0.3} dot={false} />
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
          <h3>Investering</h3>
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
          <h3>Årlig drift</h3>
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
  )
}
