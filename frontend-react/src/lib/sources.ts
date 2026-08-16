// Provenance registry for domain constants used across the app. Rendered by
// the Kjelder component (Home, Potensial, Beregn result panel, Rapport).

export interface Source {
  id: string
  label: string
  ref: string
}

export const SOURCES: Source[] = [
  {
    id: 'who',
    label: 'WHO overlevelsesminimum 13 L/person/dag',
    ref: 'WHO Technical Notes on Drinking-Water, Sanitation and Hygiene in Emergencies',
  },
  {
    id: 'met',
    label: 'Nedbørsdata: MET Frost API, stasjon Bergen Florida (SN50540) m.fl.',
    ref: 'frost.met.no',
  },
  {
    id: 'normal',
    label: 'Normalnedbør Bergen ~2 250 mm/år',
    ref: 'Norsk klimaservicesenter / MET normalperiode 1991–2020',
  },
  {
    id: 'dsb',
    label: 'Kommunal beredskapsplikt og nasjonale anbefalinger for nødvann',
    ref: 'DSB — Sivilbeskyttelsesloven §§ 14–15',
  },
  {
    id: 'klima',
    label: 'Klimapåslag (+10–20 % intensitet)',
    ref: 'Norsk klimaservicesenter, Klimaprofil Hordaland',
  },
  {
    id: 'framework',
    label: 'Metodikk, ytelsesformel V = A × R × C × e og kostnadsrammer',
    ref: 'docs/bergen_rainwater_emergency_supply.md (prosjektets rammeverk)',
  },
  {
    id: 'costs',
    label: 'Kostnadsanslag er bransjeestimater, ikke innhentede leverandørtilbud',
    ref: 'docs/bergen_rainwater_emergency_supply.md §14.2 (indikative anslag)',
  },
]
