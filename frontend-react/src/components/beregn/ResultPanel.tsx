import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { api } from '../../api/client'
import { useBeredskap } from '../../context/BeredskapsContext'
import SimulationChart from '../shared/SimulationChart'
import DrySpellsList from '../shared/DrySpellsList'
import { WaterQualityCard } from '../shared/WaterQualityCard'
import { EnergyCard } from '../shared/EnergyCard'
import { YearlyOutcomes } from '../shared/YearlyOutcomes'
import Kjelder from '../shared/Kjelder'
import { BUILDING_OPTIONS } from './buildingTypes'

function fmt(n: number, decimals = 0) {
  return n.toLocaleString('nb-NO', { maximumFractionDigits: decimals })
}

function verdictFor(daysTankEmpty: number) {
  if (daysTankEmpty === 0) return { text: 'Svært god beredskap', dot: '#6EE7B7' }
  if (daysTankEmpty < 14)  return { text: 'Tilstrekkelig beredskap', dot: '#FBBF24' }
  return                          { text: 'Sårbar forsyning', dot: '#FCA5A5' }
}

export default function ResultPanel() {
  const navigate = useNavigate()
  const {
    buildingKey, roofSource,
    simResult, isSimPending,
    population, scale, annualLiters, usageLevel, roofMaterial, station, scenario,
    roofPerBuilding, numBuildings, heightM,
  } = useBeredskap()

  const { data: config } = useQuery({ queryKey: ['config'], queryFn: api.config })

  const costsQuery = useQuery({
    queryKey: ['costs', population, scale, Math.round(annualLiters)],
    queryFn: () => api.costs(population, scale, annualLiters),
    enabled: population > 0 && annualLiters > 0,
  })
  const costs = costsQuery.data

  const totalRoofM2 = roofPerBuilding * numBuildings
  const roofDescriptor =
    roofSource === 'preset'
      ? BUILDING_OPTIONS.find(o => o.key === buildingKey)?.label.toLowerCase() ?? 'bygg'
      : `${fmt(totalRoofM2)} m² tak (målt)`

  const stationLabel = config?.stations.find(s => s.id === station)?.label

  if (!config) {
    return <div className="k-result-panel" />
  }

  const waterNeeds = config.water_needs
  const dailyNeed = population * (waterNeeds[usageLevel] ?? waterNeeds['survival_total'])
  const [minDays, recDays, robustDays] = config.defaults.tank_recommendation_days

  const summary = simResult?.summary ?? {}
  const supplyDays    = (summary['days_of_survival_supply'] ?? 0) as number
  const totalLiters   = (summary['total_collected_liters'] ?? 0) as number
  const daysTankEmpty = (summary['days_tank_empty'] ?? 0) as number
  const longestDry    = (summary['longest_dry_spell_days'] ?? 0) as number
  const dailyAvg      = totalLiters / 365

  const verdict = verdictFor(daysTankEmpty)
  const loading = isSimPending && !simResult

  return (
    <div className="k-result-panel">
      {/* Hero */}
      <div className="k-result-hero">
        <div className="k-rh-verdict">
          Beredskapsforsyning · {fmt(population)} {population === 1 ? 'person' : 'personer'} · {roofDescriptor}
        </div>
        <div className="k-rh-number">{loading ? '—' : fmt(supplyDays)}</div>
        <div className="k-rh-unit">dager med trygg vannforsyning</div>
        {!loading && (
          <div className="k-rh-badge">
            <div className="k-rh-badge-dot" style={{ background: verdict.dot }} />
            {verdict.text}
          </div>
        )}
      </div>

      {/* Metrics */}
      <div className="k-metrics-row">
        <div className="k-metric-card">
          <div className="k-mc-label">Takflate</div>
          <div className="k-mc-val">{fmt(totalRoofM2)} <span className="k-mc-unit">m²</span></div>
        </div>
        <div className="k-metric-card">
          <div className="k-mc-label">Årlig oppsamling</div>
          <div className="k-mc-val">{loading ? '—' : fmt(totalLiters)} <span className="k-mc-unit">L</span></div>
        </div>
        <div className="k-metric-card">
          <div className="k-mc-label">Daglig gjennomsnitt</div>
          <div className="k-mc-val">{loading ? '—' : fmt(dailyAvg)} <span className="k-mc-unit">L/dag</span></div>
        </div>
        <div className="k-metric-card">
          <div className="k-mc-label">Daglig behov</div>
          <div className="k-mc-val">{fmt(dailyNeed)} <span className="k-mc-unit">L/dag</span></div>
        </div>
      </div>

      <p className="k-who-note">
        {waterNeeds['survival_total']} L/person/dag dekker drikke {waterNeeds['drinking']} ·
        hygiene {waterNeeds['sanitation']} · matlaging {waterNeeds['cooking']} ·
        medisin {waterNeeds['medical']} (WHO-minimum)
      </p>

      {/* Tank recommendation */}
      <div className="k-tank-rec">
        <div>
          <div className="k-tr-eyebrow">Anbefalt tankstørrelse</div>
          <div className="k-tr-val">{fmt(dailyNeed * recDays)} L</div>
          <div className="k-tr-sub">
            Dekker {recDays} dager uten nedbør · lengste registrert: {fmt(longestDry)} d
          </div>
        </div>
        <div className="k-tr-options">
          <div className="k-tr-opt">Min: <strong>{fmt(dailyNeed * minDays)} L</strong> · {minDays} dager</div>
          <div className="k-tr-opt">Anbefalt: <strong>{fmt(dailyNeed * recDays)} L</strong> · {recDays} dager</div>
          <div className="k-tr-opt">Robust: <strong>{fmt(dailyNeed * robustDays)} L</strong> · {robustDays} dager</div>
        </div>
      </div>

      {/* Cost line */}
      {costs && (
        <div className="k-cost-line">
          <div className="k-cl-label">Anslått kostnad</div>
          <div className="k-cl-val">
            ~{fmt(costs.capital)} kr i investering · ~{fmt(costs.annual_op)} kr/år i drift
          </div>
        </div>
      )}

      {/* Chart */}
      <SimulationChart
        series={simResult?.simulation_series}
        loading={loading}
        classPrefix="k"
        stroke="var(--k-blue)"
      />

      {/* Dry spells */}
      <DrySpellsList
        spells={simResult?.dry_spells}
        loading={loading}
        classPrefix="k"
        labels={{
          title: 'Sårbare perioder',
          badge: n => `${n} tørkeperioder i år`,
          days: n => `${n} dager`,
          empty: 'Ingen lengre tørkeperioder funnet.',
        }}
      />

      {/* Water quality */}
      <WaterQualityCard material={roofMaterial} scale={scale} classPrefix="k" />

      {/* Energy — a talking point at scale; hidden for household (Phase 5 precedent) */}
      {scale !== 'household' && (
        <EnergyCard
          totalRoofM2={roofPerBuilding * numBuildings}
          heightM={heightM}
          classPrefix="k"
        />
      )}

      {/* Historical year outcomes */}
      {simResult?.yearly_outcomes && (
        <YearlyOutcomes
          outcomes={simResult.yearly_outcomes}
          classPrefix="k"
          stationLabel={stationLabel}
        />
      )}

      {/* Report */}
      <button
        className="k-roof-map-btn"
        style={{ alignSelf: 'flex-start' }}
        onClick={() => navigate('/rapport')}
        disabled={!simResult}
      >
        Generer rapport
      </button>

      {/* Kjelder */}
      <div className="k-data-note">
        <Kjelder
          ids={
            scenario === 'historical'
              ? ['who', 'met', 'framework']
              : ['who', 'met', 'framework', 'klima']
          }
        />
      </div>
    </div>
  )
}
