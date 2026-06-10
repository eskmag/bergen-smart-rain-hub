import {
  AreaChart, Area, XAxis, YAxis,
  CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer,
} from 'recharts'
import type { SimulationRow } from '../../api/client'

interface SimulationChartProps {
  series: SimulationRow[] | undefined
  loading: boolean
  // 'k' (kalkulator) or 't' (takkart) — selects the page's CSS namespace
  classPrefix: 'k' | 't'
  stroke?: string
}

export default function SimulationChart({
  series,
  loading,
  classPrefix: p,
  stroke = 'var(--color-primary)',
}: SimulationChartProps) {
  return (
    <div className={`${p}-chart-card`}>
      <div className={`${p}-chart-header`}>
        <span className={`${p}-chart-title`}>Tanknivå gjennom året</span>
        <div className={`${p}-chart-legend`}>
          <div className={`${p}-legend-item`}><div className={`${p}-legend-dot`} style={{ background: '#BFDBF7' }} />Tanknivå</div>
          <div className={`${p}-legend-item`}><div className={`${p}-legend-dot`} style={{ background: '#C1440E' }} />Kritisk 20 %</div>
        </div>
      </div>
      {loading || !series ? (
        <p className={`${p}-placeholder`}>Simulerer…</p>
      ) : (
        <ResponsiveContainer width="100%" height={160}>
          <AreaChart data={series} margin={{ top: 5, right: 6, left: -18, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#EDF0F3" />
            <XAxis dataKey="date" tickFormatter={d => d.slice(5)} tick={{ fontSize: 10 }} minTickGap={40} />
            <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} unit="%" />
            <Tooltip
              formatter={v => [`${Number(v).toFixed(1)} %`, 'Tanknivå']}
              labelFormatter={l => `Dato: ${l}`}
            />
            <ReferenceLine y={20} stroke="#C1440E" strokeDasharray="4 4" />
            <Area type="monotone" dataKey="tank_pct" stroke={stroke} fill="#BFDBF7" fillOpacity={0.6} dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
