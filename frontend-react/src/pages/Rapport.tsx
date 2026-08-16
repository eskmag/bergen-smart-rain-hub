import { Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import { useBeredskap } from '../context/BeredskapsContext'
import SimulationChart from '../components/shared/SimulationChart'
import DrySpellsList from '../components/shared/DrySpellsList'
import { WaterQualityCard } from '../components/shared/WaterQualityCard'
import { YearlyOutcomes } from '../components/shared/YearlyOutcomes'
import Kjelder from '../components/shared/Kjelder'
import { BUILDING_OPTIONS } from '../components/beregn/buildingTypes'
import '../rapport.css'

function fmt(n: number, decimals = 0) {
  return n.toLocaleString('nb-NO', { maximumFractionDigits: decimals })
}

function today() {
  return new Date().toLocaleDateString('nb-NO', { year: 'numeric', month: 'long', day: 'numeric' })
}

export default function Rapport() {
  const navigate = useNavigate()
  const {
    buildingKey, roofSource, roofPerBuilding, numBuildings,
    population, tankLiters, usageLevel, roofMaterial, station, scenario, scale,
    simResult, annualLiters,
  } = useBeredskap()

  const { data: config } = useQuery({ queryKey: ['config'], queryFn: api.config })
  const costsQuery = useQuery({
    queryKey: ['costs', population, scale, Math.round(annualLiters)],
    queryFn: () => api.costs(population, scale, annualLiters),
    enabled: population > 0 && annualLiters > 0,
  })
  const costs = costsQuery.data

  if (!simResult) {
    return (
      <div className="r-shell">
        <div className="r-empty no-print">
          <p>Kjør en beregning først.</p>
          <Link to="/beregn">Gå til kalkulatoren</Link>
        </div>
      </div>
    )
  }

  const totalRoofM2 = roofPerBuilding * numBuildings
  const buildingLabel =
    roofSource === 'preset'
      ? BUILDING_OPTIONS.find(o => o.key === buildingKey)?.label ?? 'Bygg'
      : `${fmt(totalRoofM2)} m² tak (målt på kart)`
  const materialLabel = config?.roof_materials.find(m => m.key === roofMaterial)?.label ?? roofMaterial
  const stationLabel = config?.stations.find(s => s.id === station)?.label ?? station
  const scenarioLabel = config?.climate_scenarios.find(c => c.key === scenario)?.label ?? scenario
  const waterNeeds = config?.water_needs ?? {}

  const summary = simResult.summary
  const totalLiters = (summary['total_collected_liters'] ?? 0) as number
  const daysTankEmpty = (summary['days_tank_empty'] ?? 0) as number
  const longestDry = (summary['longest_dry_spell_days'] ?? 0) as number
  const supplyDays = (summary['days_of_survival_supply'] ?? 0) as number

  return (
    <div className="r-shell">
      <div className="r-toolbar no-print">
        <Link to="/beregn">← Tilbake til kalkulatoren</Link>
        <button className="r-print-btn" onClick={() => window.print()}>Last ned som PDF</button>
      </div>

      <div className="r-page">
        <header className="r-header">
          <h1>Beredskapsrapport — regnvann som nødvannskilde</h1>
          <p className="r-date">Generert {today()}</p>
        </header>

        <section className="r-section">
          <h2>Forutsetninger</h2>
          <dl className="r-params">
            <div><dt>Bygg</dt><dd>{buildingLabel}</dd></div>
            <div><dt>Takareal</dt><dd>{fmt(totalRoofM2)} m²</dd></div>
            <div><dt>Takmateriale</dt><dd>{materialLabel}</dd></div>
            <div><dt>Tankstørrelse</dt><dd>{fmt(tankLiters)} L</dd></div>
            <div><dt>Personer</dt><dd>{fmt(population)}</dd></div>
            <div><dt>Forbruksnivå</dt><dd>{waterNeeds[usageLevel] ?? '—'} L/person/dag</dd></div>
            <div><dt>Værstasjon</dt><dd>{stationLabel}</dd></div>
            <div><dt>Klimascenario</dt><dd>{scenarioLabel}</dd></div>
          </dl>
        </section>

        <section className="r-section">
          <h2>Nøkkelresultater</h2>
          <dl className="r-params">
            <div><dt>Dager med trygg vannforsyning</dt><dd>{fmt(supplyDays)}</dd></div>
            <div><dt>Årlig oppsamling</dt><dd>{fmt(totalLiters)} L</dd></div>
            <div><dt>Dager med tom tank</dt><dd>{fmt(daysTankEmpty)}</dd></div>
            <div><dt>Lengste tørkeperiode</dt><dd>{fmt(longestDry)} dager</dd></div>
          </dl>
        </section>

        <section className="r-section">
          <SimulationChart series={simResult.simulation_series} loading={false} classPrefix="r" />
        </section>

        <section className="r-section">
          <DrySpellsList
            spells={simResult.dry_spells}
            classPrefix="r"
            labels={{
              title: 'Sårbare perioder',
              badge: n => `${n} tørkeperioder i år`,
              days: n => `${n} dager`,
              empty: 'Ingen lengre tørkeperioder funnet.',
            }}
          />
        </section>

        {simResult.yearly_outcomes.length > 1 && (
          <section className="r-section">
            <YearlyOutcomes outcomes={simResult.yearly_outcomes} classPrefix="r" stationLabel={stationLabel} />
          </section>
        )}

        <section className="r-section">
          <WaterQualityCard material={roofMaterial} scale={scale} classPrefix="r" />
        </section>

        {costs && (
          <section className="r-section">
            <h2>Kostnadsanslag</h2>
            <dl className="r-params">
              <div><dt>Investering</dt><dd>~{fmt(costs.capital)} kr</dd></div>
              <div><dt>Årlig drift</dt><dd>~{fmt(costs.annual_op)} kr/år</dd></div>
            </dl>
          </section>
        )}

        <section className="r-section">
          <Kjelder />
        </section>

        <footer className="r-disclaimer">
          Beregningene er estimater basert på historiske målinger og dokumenterte forutsetninger
          — ikke et dimensjoneringsgrunnlag.
        </footer>
      </div>

      <div className="r-toolbar-bottom no-print">
        <button onClick={() => navigate('/beregn')}>Endre forutsetninger</button>
      </div>
    </div>
  )
}
