import type { DrySpell } from '../../api/client'

interface DrySpellLabels {
  title: string
  badge: (count: number) => string
  days: (days: number) => string
  empty?: string
}

interface DrySpellsListProps {
  spells: DrySpell[] | undefined
  loading?: boolean
  // 'k' (kalkulator) or 't' (takkart) — selects the page's CSS namespace
  classPrefix: 'k' | 't'
  // bokmål on /beregn, nynorsk on /takkart
  labels: DrySpellLabels
  hideWhenEmpty?: boolean
}

export default function DrySpellsList({
  spells,
  loading = false,
  classPrefix: p,
  labels,
  hideWhenEmpty = false,
}: DrySpellsListProps) {
  const sorted = [...(spells ?? [])].sort((a, b) => b.days - a.days)
  const maxDays = sorted[0]?.days ?? 1
  const top = sorted.slice(0, 3)

  if (hideWhenEmpty && top.length === 0) return null

  return (
    <div className={`${p}-dry-spells-card`}>
      <div className={`${p}-ds-header`}>
        <span className={`${p}-ds-title`}>{labels.title}</span>
        {!loading && (
          <span className={`${p}-ds-badge`}>{labels.badge(sorted.length)}</span>
        )}
      </div>
      {loading ? (
        <p className={`${p}-placeholder`}>Beregner…</p>
      ) : top.length === 0 ? (
        <p className={`${p}-ds-empty`}>{labels.empty}</p>
      ) : (
        top.map((s, i) => (
          <div className={`${p}-ds-row`} key={i}>
            <div>
              <div className={`${p}-ds-days`}>{labels.days(s.days)}</div>
              <div className={`${p}-ds-dates`}>{s.start} — {s.end}</div>
            </div>
            <div className={`${p}-ds-bar-wrap`}>
              <div className={`${p}-ds-bar`}>
                <div className={`${p}-ds-bar-fill`} style={{ width: `${(s.days / maxDays) * 100}%` }} />
              </div>
            </div>
            {i === 0
              ? <div className={`${p}-ds-tag-longest`}>Lengste</div>
              : <div className={`${p}-ds-tag-muted`}>–</div>}
          </div>
        ))
      )}
    </div>
  )
}
