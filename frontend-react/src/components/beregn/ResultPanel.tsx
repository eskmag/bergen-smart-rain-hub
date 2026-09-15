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
import { tankForDays } from '../../lib/rainwater'

function fmt(n: number, decimals = 0) {
  return n.toLocaleString('nb-NO', { maximumFractionDigits: decimals })
}

// Yearly volumes are estimates — show them to the nearest 100 L
function fmtVolume(liters: number) {
  return fmt(Math.round(liters / 100) * 100)
}

function verdictFor(daysTankEmpty: number) {
  if (daysTankEmpty === 0) return { text: 'Svært god beredskap', dot: '#6EE7B7' }
  if (daysTankEmpty < 14)  return { text: 'Tilstrekkelig beredskap', dot: '#FBBF24' }
  return                          { text: 'Sårbar forsyning', dot: '#FCA5A5' }
}

// Answer first, details one click away: the hero, one plain sentence and the
// chart are always visible; everything else sits in «Flere detaljer» and in
// the full report (/rapport).
export default function ResultPanel() {
  const navigate = useNavigate()
  const {
    buildingKey, roofSource,
    simResult, isSimPending, isStale,
    population, scale, annualLiters, usageLevel, roofMaterial, station, scenario,
    roofPerBuilding, numBuildings, heightM, tankLiters,
  } = useBeredskap()

  const { data: config } = useQuery({ queryKey: ['config'], queryFn: api.config })

  const costsQuery = useQuery({
    queryKey: ['costs', population, scale, Math.round(annualLiters)],
    queryFn: () => api.costs(population, scale, annualLiters),
    enabled: population > 0 && annualLiters > 0,
  })
  const costs = costsQuery.data

  // Same query key as WaterQualityCard, so this is served from cache. An
  // unsuitable roof is safety information and must not hide behind a toggle.
  const { data: treatment } = useQuery({
    queryKey: ['treatment', roofMaterial, scale],
    queryFn: () => api.treatment(roofMaterial, scale),
    enabled: Boolean(roofMaterial) && Boolean(scale),
  })

  const totalRoofM2 = roofPerBuilding * numBuildings
  const roofDescriptor =
    roofSource === 'preset'
      ? BUILDING_OPTIONS.find(o => o.key === buildingKey)?.label.toLowerCase() ?? 'bygg'
      : `${fmt(totalRoofM2)} m² tak`

  const stationLabel = config?.stations.find(s => s.id === station)?.label

  if (!config) {
    return <div className="k-result-panel" />
  }

  const waterNeeds = config.water_needs
  const dailyNeed = population * (waterNeeds[usageLevel] ?? waterNeeds['survival_total'])
  const recDays = config.defaults.tank_recommendation_days[1]

  // How long a full tank lasts with no rain at all — the concrete beredskap answer.
  const tankDays = dailyNeed > 0 ? Math.floor(tankLiters / dailyNeed) : 0
  // Same size the «30 dager» preset (and the default tank) uses, so the
  // recommendation only shows when a smaller tank was picked by hand.
  const recommendedLiters = tankForDays(dailyNeed, recDays)

  const summary = simResult?.summary ?? {}
  const totalLiters   = (summary['total_collected_liters'] ?? 0) as number
  const storedLiters  = (summary['stored_liters'] ?? 0) as number
  const overflowLiters = (summary['overflow_liters'] ?? 0) as number
  const daysTankEmpty = (summary['days_tank_empty'] ?? 0) as number
  const longestDry    = (summary['longest_dry_spell_days'] ?? 0) as number

  const verdict = verdictFor(daysTankEmpty)
  const loading = isSimPending && !simResult

  return (
    <div className="k-result-panel">
      {/* Hero */}
      <div className="k-result-hero">
        <div className="k-rh-verdict">
          {fmt(population)} {population === 1 ? 'person' : 'personer'} · {roofDescriptor}
        </div>
        {!loading && isStale && <div className="k-rh-updating">Oppdaterer…</div>}
        <div className="k-rh-number">{fmt(tankDays)}</div>
        <div className="k-rh-unit">
          {tankDays === 1 ? 'dag' : 'dager'} med vann fra full tank, uten regn
        </div>
        {!loading && (
          <div className="k-rh-badge">
            <div className="k-rh-badge-dot" style={{ background: verdict.dot }} />
            {verdict.text}
          </div>
        )}
        {!loading && (
          <div className="k-rh-collect">
            {overflowLiters < 100 ? (
              <>Tanken din fanger alle <strong>{fmtVolume(totalLiters)} liter</strong> taket gir i året.</>
            ) : (
              <>
                Taket gir <strong>{fmtVolume(totalLiters)} liter</strong> i året.
                Tanken din fanger <strong>{fmtVolume(storedLiters)} liter</strong> – resten renner over.
              </>
            )}
          </div>
        )}
      </div>

      {/* The answer in one sentence */}
      {!loading && (
        <p className="k-summary">
          {daysTankEmpty === 0
            ? 'Regnet fyller tanken opp igjen, og den gikk aldri tom i løpet av året. '
            : `Tanken var tom ${fmt(daysTankEmpty)} ${daysTankEmpty === 1 ? 'dag' : 'dager'} i løpet av året. `}
          Den lengste perioden uten regn varte {fmt(longestDry)} dager.
          {tankLiters < recommendedLiters && (
            <> Vi anbefaler minst <strong>{fmt(recommendedLiters)} liter</strong>, nok til omtrent {recDays} dager.</>
          )}
        </p>
      )}

      {treatment && !treatment.potable && (
        <p className="k-warning" role="alert">{treatment.note}</p>
      )}

      <SimulationChart
        series={simResult?.simulation_series}
        loading={loading}
        classPrefix="k"
        stroke="var(--k-blue)"
      />

      <details className="k-details">
        <summary>Flere detaljer</summary>
        <div className="k-details-body">
          {costs && (
            <div className="k-cost-line">
              <div className="k-cl-label">Anslått kostnad</div>
              <div className="k-cl-val">
                ~{fmt(costs.capital)} kr i investering · ~{fmt(costs.annual_op)} kr/år i drift
              </div>
            </div>
          )}

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

          <WaterQualityCard material={roofMaterial} scale={scale} classPrefix="k" />

          {simResult?.yearly_outcomes && (
            <YearlyOutcomes
              outcomes={simResult.yearly_outcomes}
              classPrefix="k"
              stationLabel={stationLabel}
            />
          )}

          {/* Energy — a talking point at scale; hidden for household (Phase 5 precedent) */}
          {scale !== 'household' && (
            <EnergyCard totalRoofM2={totalRoofM2} heightM={heightM} classPrefix="k" />
          )}
        </div>
      </details>

      <button
        className="k-roof-map-btn"
        style={{ alignSelf: 'flex-start' }}
        onClick={() => navigate('/rapport')}
        disabled={!simResult}
      >
        Lag rapport
      </button>

      <div className="k-data-note">
        <Kjelder
          ids={
            scenario === 'historical'
              ? ['who', 'met', 'framework', 'costs']
              : ['who', 'met', 'framework', 'klima', 'costs']
          }
        />
      </div>
    </div>
  )
}
