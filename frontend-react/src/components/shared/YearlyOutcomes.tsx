import type { YearlyOutcome } from '../../api/client'

interface YearlyOutcomesProps {
  outcomes: YearlyOutcome[]
  // 'k' (kalkulator) or 't' (takkart) — selects the page's CSS namespace
  classPrefix: 'k' | 't'
  stationLabel?: string
}

function rankByWorst(outcomes: YearlyOutcome[]): YearlyOutcome[] {
  // Sort ascending by min_tank_pct (worst = lowest); tiebreak: longest_dry_spell_days desc
  return [...outcomes].sort((a, b) => {
    if (a.min_tank_pct !== b.min_tank_pct) return a.min_tank_pct - b.min_tank_pct
    return b.longest_dry_spell_days - a.longest_dry_spell_days
  })
}

function fmt(n: number, decimals = 0) {
  return n.toLocaleString('nb-NO', { maximumFractionDigits: decimals })
}

export function YearlyOutcomes({ outcomes, classPrefix: p, stationLabel }: YearlyOutcomesProps) {
  if (outcomes.length < 2) return null

  const ranked = rankByWorst(outcomes)
  const worst = ranked[0]
  const best = ranked[ranked.length - 1]
  const median = ranked[Math.floor(ranked.length / 2)]

  const rows = [
    { label: 'Beste år', row: best },
    { label: 'Median', row: median },
    { label: 'Verste år', row: worst },
  ]

  const headline = `Basert på ${outcomes.length} år med målte data${stationLabel ? ` frå ${stationLabel}` : ''}.`

  return (
    <div className={`${p}-dry-spells-card`}>
      <div className={`${p}-ds-header`}>
        <span className={`${p}-ds-title`}>Historiske år</span>
      </div>
      <p style={{ margin: '0.5rem 0 0.75rem', fontSize: '0.85rem', color: 'var(--text-muted, #6b7280)' }}>
        {headline}
      </p>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border-subtle, #e5e7eb)' }}>
            <th style={{ textAlign: 'left', paddingBottom: '0.35rem', fontWeight: 600 }}></th>
            <th style={{ textAlign: 'right', paddingBottom: '0.35rem', fontWeight: 600 }}>År</th>
            <th style={{ textAlign: 'right', paddingBottom: '0.35rem', fontWeight: 600 }}>Min. tanknivå (%)</th>
            <th style={{ textAlign: 'right', paddingBottom: '0.35rem', fontWeight: 600 }}>Lengste tørkeperiode (dager)</th>
            <th style={{ textAlign: 'right', paddingBottom: '0.35rem', fontWeight: 600 }}>Dager tom tank</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(({ label, row }) => (
            <tr
              key={`${label}-${row.year}`}
              style={{ borderBottom: '1px solid var(--border-subtle, #f3f4f6)' }}
            >
              <td style={{ padding: '0.35rem 0', color: 'var(--text-muted, #6b7280)' }}>{label}</td>
              <td style={{ textAlign: 'right', padding: '0.35rem 0' }}>{row.year}</td>
              <td style={{ textAlign: 'right', padding: '0.35rem 0' }}>{fmt(row.min_tank_pct * 100, 1)}</td>
              <td style={{ textAlign: 'right', padding: '0.35rem 0' }}>{row.longest_dry_spell_days}</td>
              <td style={{ textAlign: 'right', padding: '0.35rem 0' }}>{row.days_tank_empty}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
