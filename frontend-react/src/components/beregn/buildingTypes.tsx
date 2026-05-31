// Building options for the Beredskapskalkulator. Each maps to a backend
// preset key (see backend/analysis.py). Icons are inline SVGs ported from
// the kalkulator mockup. `detail` shows the preset roof area.

import type { ReactNode } from 'react'

export interface BuildingOption {
  key: string
  scale: 'household' | 'neighbourhood'
  label: string
  detail: string
  icon: ReactNode
}

const svgProps = {
  width: 22,
  height: 22,
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.5,
  viewBox: '0 0 24 24',
}

export const BUILDING_OPTIONS: BuildingOption[] = [
  {
    key: 'enebolig',
    scale: 'household',
    label: 'Enebolig',
    detail: '120 m² tak',
    icon: (
      <svg {...svgProps}>
        <path d="M3 12L12 3l9 9" />
        <path d="M9 21V12h6v9" />
        <path d="M3 12v9h18v-9" />
      </svg>
    ),
  },
  {
    key: 'rekkehus',
    scale: 'household',
    label: 'Rekkehus',
    detail: '80 m² tak',
    icon: (
      <svg {...svgProps}>
        <path d="M1 21h22" />
        <path d="M3 21V9l6-6 6 6v12" />
        <path d="M15 21V11l4-4 4 4v10" />
        <path d="M9 21v-6h4v6" />
      </svg>
    ),
  },
  {
    key: 'leilighet_liten',
    scale: 'neighbourhood',
    label: 'Liten blokk',
    detail: '300 m² tak',
    icon: (
      <svg {...svgProps}>
        <rect x="3" y="3" width="18" height="18" rx="1" />
        <path d="M3 9h18M3 15h18M9 3v18M15 3v18" />
      </svg>
    ),
  },
  {
    key: 'leilighet_stor',
    scale: 'neighbourhood',
    label: 'Stor blokk',
    detail: '800 m² tak',
    icon: (
      <svg {...svgProps}>
        <rect x="2" y="3" width="20" height="18" rx="1" />
        <path d="M2 9h20M8 3v6M16 3v6M2 15h20M8 15v6M16 15v6" />
      </svg>
    ),
  },
  {
    key: 'barneskole',
    scale: 'neighbourhood',
    label: 'Barneskole',
    detail: '800 m² tak',
    icon: (
      <svg {...svgProps}>
        <path d="M3 21V7l9-4 9 4v14" />
        <path d="M3 21h18" />
        <rect x="9" y="13" width="6" height="8" />
        <path d="M9 9h.01M15 9h.01M9 13h.01M15 13h.01" />
      </svg>
    ),
  },
  {
    key: 'idrettshall',
    scale: 'neighbourhood',
    label: 'Idrettshall',
    detail: '2 000 m² tak',
    icon: (
      <svg {...svgProps}>
        <path d="M2 12 Q12 4 22 12" />
        <rect x="2" y="12" width="20" height="9" />
        <path d="M6 12v9M18 12v9M2 17h20" />
        <path d="M9 21v-4h6v4" />
      </svg>
    ),
  },
]
