interface MetricCardProps {
  label: string
  value: string
  help?: string
  highlighted?: boolean
}

export function MetricCard({ label, value, help, highlighted }: MetricCardProps) {
  return (
    <div className={`metric-card${highlighted ? ' highlighted' : ''}`} title={help}>
      <div className="metric-card-label">{label}</div>
      <div className="metric-card-value">{value}</div>
    </div>
  )
}
