import { useState } from 'react'
import { useBeredskap } from '../context/BeredskapsContext'

const SEVERITY_COLORS: Record<string, string> = {
  Kritisk: '#C1292E',
  Høy: '#E8963E',
  Middels: '#2B7A8E',
}

export default function Risiko() {
  const { riskResult, isRiskPending, simResult } = useBeredskap()
  const [openRisk, setOpenRisk] = useState<string | null>(null)
  const [openCcp, setOpenCcp] = useState<string | null>(null)

  if (isRiskPending || !riskResult) {
    return (
      <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
        {simResult ? 'Vurderer risikoer…' : 'Venter på simuleringsresultat…'}
      </p>
    )
  }

  return (
    <>
      <p className="subtitle" style={{ marginBottom: '1rem' }}>
        Systematisk risikovurdering basert på norske og internasjonale standarder, tilpasset ditt scenario.
      </p>

      <h2>Risikoer for ditt scenario</h2>
      <p className="caption">Rangert etter relevans for ditt oppsett. Klikk for å se detaljer og tiltak.</p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', margin: '1rem 0' }}>
        {riskResult.assessed_risks.map(risk => {
          const color = SEVERITY_COLORS[risk.overall] ?? '#666'
          const isOpen = openRisk === risk.name
          return (
            <div key={risk.name} style={{ border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
              <button
                onClick={() => setOpenRisk(isOpen ? null : risk.name)}
                style={{
                  width: '100%', textAlign: 'left', padding: '0.75rem 1rem',
                  background: 'var(--color-surface)', border: 'none', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', gap: '0.75rem',
                  fontFamily: 'var(--font-body)',
                }}
              >
                <span style={{
                  background: color, color: '#fff', padding: '2px 8px',
                  borderRadius: '4px', fontSize: '0.8rem', whiteSpace: 'nowrap',
                }}>{risk.overall}</span>
                <span style={{ fontWeight: 500 }}>{risk.name}</span>
                <span style={{ marginLeft: 'auto', color: 'var(--color-text-muted)' }}>{isOpen ? '▲' : '▼'}</span>
              </button>
              {isOpen && (
                <div style={{ padding: '0.75rem 1rem', borderTop: '1px solid var(--color-border)', background: 'var(--color-card)' }}>
                  <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', marginBottom: '0.5rem', fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
                    <span><strong>Sannsynlighet:</strong> {risk.likelihood}</span>
                    <span><strong>Konsekvens:</strong> {risk.impact}</span>
                    <span><strong>Kategori:</strong> {riskResult.category_labels[risk.category] ?? risk.category}</span>
                  </div>
                  {risk.reason && (
                    <div className="alert alert-info" style={{ marginBottom: '0.5rem', fontSize: '0.85rem' }}>
                      Relevant for ditt scenario: {risk.reason}
                    </div>
                  )}
                  <p style={{ fontSize: '0.9rem' }}><strong>Tiltak:</strong> {risk.mitigation}</p>
                </div>
              )}
            </div>
          )
        })}
      </div>

      <hr className="section-divider" />

      <h2>Komplett risikomatrise</h2>
      <table>
        <thead>
          <tr><th>Risiko</th><th>Kategori</th><th>Sannsynlighet</th><th>Konsekvens</th><th>Samlet</th></tr>
        </thead>
        <tbody>
          {riskResult.assessed_risks.map(r => (
            <tr key={r.name}>
              <td>{r.name}</td>
              <td>{riskResult.category_labels[r.category] ?? r.category}</td>
              <td>{r.likelihood}</td>
              <td>{r.impact}</td>
              <td style={{ color: SEVERITY_COLORS[r.overall] ?? 'var(--color-text)', fontWeight: 600 }}>{r.overall}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <hr className="section-divider" />

      <h2>Kritiske kontrollpunkter (HACCP)</h2>
      <p className="caption">
        For systemer beregnet på offentlig bruk kreves en formell HACCP-tilnærming, i henhold til norsk Vannforskrift.
      </p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', margin: '1rem 0' }}>
        {riskResult.ccps.map(ccp => {
          const isOpen = openCcp === ccp.id
          return (
            <div key={ccp.id} style={{ border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
              <button
                onClick={() => setOpenCcp(isOpen ? null : ccp.id)}
                style={{
                  width: '100%', textAlign: 'left', padding: '0.75rem 1rem',
                  background: 'var(--color-surface)', border: 'none', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', gap: '0.5rem',
                  fontFamily: 'var(--font-body)',
                }}
              >
                <span style={{ fontWeight: 600, color: 'var(--color-primary)' }}>{ccp.id}</span>
                <span style={{ fontWeight: 500 }}>{ccp.name}</span>
                <span style={{ marginLeft: 'auto', color: 'var(--color-text-muted)' }}>{isOpen ? '▲' : '▼'}</span>
              </button>
              {isOpen && (
                <div style={{ padding: '0.75rem 1rem', borderTop: '1px solid var(--color-border)', background: 'var(--color-card)' }}>
                  <p style={{ margin: '0 0 0.4rem', fontSize: '0.9rem' }}><strong>Beskrivelse:</strong> {ccp.description}</p>
                  <p style={{ margin: 0, fontSize: '0.9rem' }}><strong>Kontrollmål:</strong> {ccp.control_measure}</p>
                </div>
              )}
            </div>
          )
        })}
      </div>

      <hr className="section-divider" />

      <h2>Bergen-spesifikke risikoer</h2>
      <div className="grid-2">
        <div>
          <h3>Eldre bygningsstock</h3>
          <p className="caption" style={{ lineHeight: 1.6 }}>
            Bergen har en betydelig andel pre-1970 trehus med blybeslag og blylodde renner, gamle malte
            overflater med blybasert maling, og noe asbestsement-taktekning. En bygningsvis kartlegging
            anbefales før implementering av nabolags- eller større systemer.
          </p>
        </div>
        <div>
          <h3>Kyst- og bymiljø</h3>
          <p className="caption" style={{ lineHeight: 1.6 }}>
            Nærhet til sjøen introduserer marin aerosol (saltavsetning på tak), måseforurensning
            (Campylobacter- og Salmonella-risiko), og tungmetaller fra historisk industriell
            virksomhet i Laksevåg, Dokken og Nøstet.
          </p>
        </div>
      </div>
    </>
  )
}
