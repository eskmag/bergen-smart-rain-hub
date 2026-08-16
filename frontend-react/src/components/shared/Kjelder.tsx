import { SOURCES } from '../../lib/sources'

interface KjelderProps {
  // Restrict to a subset of SOURCES by id; omit to show all.
  ids?: string[]
}

export default function Kjelder({ ids }: KjelderProps) {
  const sources = ids ? SOURCES.filter(s => ids.includes(s.id)) : SOURCES

  return (
    <details style={{ fontSize: '0.85rem', color: 'var(--text-muted, #6b7280)' }}>
      <summary style={{ cursor: 'pointer', fontWeight: 500 }}>Kjelder og forutsetninger</summary>
      <ul style={{ margin: '0.6rem 0 0', paddingLeft: '1.25rem' }}>
        {sources.map(s => (
          <li key={s.id} style={{ margin: '0.3rem 0' }}>
            {s.label} — <em>{s.ref}</em>
          </li>
        ))}
      </ul>
    </details>
  )
}
