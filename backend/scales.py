"""Scale models for rainwater supply systems.

Based on docs/bergen_rainwater_emergency_supply.md, section 9.
Defines three scales (household, neighbourhood, critical infrastructure)
with reference data used by the preparedness, risk, and cost pages.
"""

from dataclasses import dataclass
from typing import Literal

ScaleKey = Literal["household", "neighbourhood", "infrastructure"]


@dataclass(frozen=True)
class ScaleSpec:
    key: str
    label: str
    description: str
    typical_population: tuple
    typical_tank_liters: tuple
    typical_buildings: tuple
    treatment_level: str
    governance_note: str
    cost_range_nok: tuple


SCALES: dict = {
    "household": ScaleSpec(
        key="household",
        label="Husholdning",
        description=(
            "Enkelt bygg — enebolig, rekkehus eller borettslag. "
            "Lav vedlikeholdsbyrde, beskjedne tankstørrelser, individuell eller borettslag-drift."
        ),
        typical_population=(1, 60),
        typical_tank_liters=(1_500, 3_000),
        typical_buildings=(1, 1),
        treatment_level="3-trinns gravitasjonsfilter (sediment + aktivt kull + keramisk)",
        governance_note="Individuell eier eller borettslag",
        cost_range_nok=(15_000, 45_000),
    ),
    "neighbourhood": ScaleSpec(
        key="neighbourhood",
        label="Nabolag",
        description=(
            "Flere bygg som mater en felles tank. Typisk et borettslag-kluster "
            "eller kvartal med 5–20 bygg og felles gravitasjonsdistribusjon."
        ),
        typical_population=(100, 500),
        typical_tank_liters=(10_000, 50_000),
        typical_buildings=(5, 20),
        treatment_level="Sediment + aktivt kull + UF-membran + UV",
        governance_note="Borettslag eller grunneierlag",
        cost_range_nok=(800_000, 2_500_000),
    ),
    "infrastructure": ScaleSpec(
        key="infrastructure",
        label="Kritisk infrastruktur",
        description=(
            "Enkeltanlegg med samfunnskritisk funksjon — sykehus, skole, brannstasjon, "
            "rådhus. Krever full behandlingskjede, automatisert overvåking og "
            "regelverksetterlevelse etter Drikkevannsforskriften."
        ),
        typical_population=(200, 2_000),
        typical_tank_liters=(50_000, 500_000),
        typical_buildings=(1, 1),
        treatment_level="Full behandlingskjede (sediment + aktivt kull + UF + UV + restklor)",
        governance_note="Offentlig virksomhet / kritisk infrastruktur-eier",
        cost_range_nok=(500_000, 8_000_000),
    ),
}


# Building preset keys (from backend.analysis.BUILDING_PRESETS) appropriate per scale.
SCALE_PRESETS: dict = {
    "household": ["enebolig", "rekkehus", "leilighet_liten", "leilighet_stor"],
    "neighbourhood": ["leilighet_liten", "leilighet_stor", "rekkehus"],
    "infrastructure": [],  # uses INFRASTRUCTURE_FACILITIES
}


# Named Bergen facility presets from docs section 9.3.
INFRASTRUCTURE_FACILITIES: dict = {
    "haukeland": {
        "label": "Haukeland universitetssjukehus",
        "roof_area_m2": 25_000,
        "default_people": 2_000,
        "height_m": 30,
        "description": "Stort universitetssykehus — kritisk helsetjeneste, stor takflate.",
    },
    "sykehjem": {
        "label": "Sykehjem",
        "roof_area_m2": 1_500,
        "default_people": 100,
        "height_m": 10,
        "description": "Sårbar brukergruppe med høyt vannbehov. ~30 anlegg i Bergen kommune.",
    },
    "barneskole": {
        "label": "Barneskole (krisesenter)",
        "roof_area_m2": 800,
        "default_people": 300,
        "height_m": 8,
        "description": "Fungerer som evakueringssted i kriser. Stor takflate, eksisterende infrastruktur.",
    },
    "brannstasjon": {
        "label": "Brannstasjon",
        "roof_area_m2": 1_200,
        "default_people": 50,
        "height_m": 8,
        "description": "Må være fullt operativ under krise — nødetat.",
    },
    "radhus": {
        "label": "Bergen rådhus",
        "roof_area_m2": 2_000,
        "default_people": 500,
        "height_m": 25,
        "description": "Kontinuitet i offentlig styring og krisehåndtering.",
    },
    "vannverk": {
        "label": "Vannverk / teknisk bygg",
        "roof_area_m2": 1_000,
        "default_people": 30,
        "height_m": 10,
        "description": "Infrastruktur for vannforsyning — egen beredskap.",
    },
}


def aggregate_neighbourhood(preset: dict, building_count: int) -> dict:
    """Return an aggregated preset: N copies of one building type.

    Roof area and default_people are multiplied by building_count.
    Height is unchanged (per-building). The label/description are rewritten
    to reflect the aggregation so the UI shows "10 × Boligblokk".
    """
    if building_count < 1:
        raise ValueError("building_count must be >= 1")

    base_label = preset["label"]
    return {
        "label": f"{building_count} × {base_label}" if building_count > 1 else base_label,
        "roof_area_m2": preset["roof_area_m2"] * building_count,
        "default_people": preset["default_people"] * building_count,
        "height_m": preset["height_m"],
        "description": (
            f"{building_count} bygg av type «{base_label}» med felles tank. "
            f"Samlet takareal {preset['roof_area_m2'] * building_count:,} m²."
        ) if building_count > 1 else preset["description"],
        "building_count": building_count,
    }
