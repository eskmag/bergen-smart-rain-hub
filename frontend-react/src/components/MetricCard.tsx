interface MetricCardProps {
  label: string
  value: string
  help?: string
  highlighted?: boolean
}

export function MetricCard({ label, value, help, highlighted }: MetricCardProps) {
  return (
    <div
      title={help}
      style={{
        background: highlighted ? '#f0f7ff' : '#f8f9fa',
        border: `1px solid ${highlighted ? '#2E86AB' : '#dee2e6'}`,
        borderRadius: '0.5rem',
        padding: '1rem',
        textAlign: 'center',
      }}
    >
      <div style={{ fontSize: '0.8rem', color: '#6c757d', marginBottom: '0.25rem' }}>{label}</div>
      <div style={{ fontSize: '1.4rem', fontWeight: 700 }}>{value}</div>
    </div>
  )
}
