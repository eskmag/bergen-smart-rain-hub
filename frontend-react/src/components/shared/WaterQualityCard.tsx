import { useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'

const RISK_LABELS: Record<string, string> = {
  lav: 'Lav risiko',
  middels: 'Middels risiko',
  høy: 'Høy risiko',
  uegnet: 'Uegnet',
}

interface WaterQualityCardProps {
  material: string
  scale: string
  // 'k' (kalkulator) or 't' (takkart) — selects the page's CSS namespace
  prefix: string
}

export function WaterQualityCard({ material, scale, prefix: p }: WaterQualityCardProps) {
  const { data } = useQuery({
    queryKey: ['treatment', material, scale],
    queryFn: () => api.treatment(material, scale),
    enabled: Boolean(material) && Boolean(scale),
  })

  if (!data) return null

  return (
    <div className={`${p}-dry-spells-card`}>
      <div className={`${p}-ds-header`}>
        <span className={`${p}-ds-title`}>Vannkvalitet og rensing</span>
      </div>
      <p style={{ margin: '0.5rem 0' }}>
        <strong>{data.material_label}</strong> — {RISK_LABELS[data.risk_class] ?? data.risk_class}
      </p>
      {data.potable ? (
        <>
          <ul style={{ margin: '0.25rem 0 0.5rem 1.25rem', padding: 0 }}>
            {data.barriers.map((b) => (
              <li key={b}>{b}</li>
            ))}
          </ul>
          <p style={{ margin: '0.25rem 0 0' }}>
            Estimert tilleggskostnad for rensing:{' '}
            {data.cost_low_nok.toLocaleString('nb-NO')}–
            {data.cost_high_nok.toLocaleString('nb-NO')} kr
          </p>
        </>
      ) : (
        <p style={{ margin: '0.25rem 0 0', color: '#DC2626' }}>{data.note}</p>
      )}
    </div>
  )
}
