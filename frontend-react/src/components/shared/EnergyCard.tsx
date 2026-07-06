import { useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'

interface EnergyCardProps {
  totalRoofM2: number
  heightM: number
  // 'k' (kalkulator) or 't' (takkart) — selects the page's CSS namespace
  classPrefix: 'k' | 't'
}

function fmt(n: number, decimals = 0) {
  return n.toLocaleString('nb-NO', { maximumFractionDigits: decimals })
}

export function EnergyCard({ totalRoofM2, heightM, classPrefix: p }: EnergyCardProps) {
  const { data } = useQuery({
    queryKey: ['energy', Math.round(totalRoofM2), heightM],
    queryFn: () => api.energy(totalRoofM2, heightM),
    enabled: totalRoofM2 > 0 && heightM > 0,
  })

  if (!data) return null

  return (
    <div className={`${p}-dry-spells-card`}>
      <div className={`${p}-ds-header`}>
        <span className={`${p}-ds-title`}>Energi og klimagevinst</span>
      </div>
      <p style={{ margin: '0.5rem 0' }}>
        Dobbel nytte: fordrøyning av overvann i normaldrift, beredskapsvann i krise.
        Fallenergien i vannet er en bonus:
      </p>
      <ul style={{ margin: '0.25rem 0 0.5rem 1.25rem', padding: 0 }}>
        <li>
          <strong>{fmt(data.annual_energy_kwh, 1)} kWh/år</strong> potensiell energi
          ({fmt(data.annual_liters)} L fra {heightM} m høyde)
        </li>
        <li>
          CO₂-ekvivalent: {fmt(data.co2_offset_g['NO'])} g (norsk strømmiks) ·{' '}
          {fmt(data.co2_offset_g['EU'])} g (EU-miks)
        </li>
        <li>
          Tilsvarer ≈ {fmt(data.equivalents['phone_charges'])} telefonladinger eller{' '}
          {fmt(data.equivalents['led_bulb_hours'])} timer LED-lys
        </li>
      </ul>
    </div>
  )
}
