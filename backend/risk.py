"""Risk assessment data and scenario-aware risk evaluation.

Based on the framework in docs/bergen_rainwater_emergency_supply.md, sections 8.1–8.4.
"""

from dataclasses import dataclass


@dataclass
class Risk:
    name: str
    category: str  # vannkvalitet, infrastruktur, drift, miljø, regelverk
    likelihood: str  # Lav, Middels, Høy
    impact: str  # Middels, Høy, Kritisk
    overall: str  # Middels, Høy, Kritisk
    mitigation: str
    relevance_tags: tuple = ()  # tags for scenario-based filtering


RISKS = [
    Risk(
        name="Takforurensning (metaller, kjemikalier)",
        category="vannkvalitet",
        likelihood="Høy",
        impact="Høy",
        overall="Kritisk",
        mitigation="Kartlegging av takmaterialer, first-flush, aktivt kull, RO for risikobygg.",
        relevance_tags=("old_building", "metal_roof"),
    ),
    Risk(
        name="Mikrobiologisk forurensning i lagret vann",
        category="vannkvalitet",
        likelihood="Høy",
        impact="Høy",
        overall="Kritisk",
        mitigation="Flerbarrierebehandling, regelmessig rengjøring, restklor.",
        relevance_tags=("large_tank",),
    ),
    Risk(
        name="Langvarig tørkeperiode overstiger lagringskapasitet",
        category="infrastruktur",
        likelihood="Middels",
        impact="Høy",
        overall="Høy",
        mitigation="Konservativ dimensjonering av lagring, rasjoneringsplan.",
        relevance_tags=("small_tank", "high_population"),
    ),
    Risk(
        name="Strømbrudd deaktiverer behandlingsutstyr",
        category="infrastruktur",
        likelihood="Middels",
        impact="Høy",
        overall="Høy",
        mitigation="Gravitasjonsbasert/passiv behandling som grunnsystem; UV/RO kun som tillegg.",
        relevance_tags=("infrastructure_scale",),
    ),
    Risk(
        name="Algevekst i lagringstanker",
        category="vannkvalitet",
        likelihood="Høy",
        impact="Middels",
        overall="Høy",
        mitigation="Full lysekskludering, isolasjon av tank, restklor.",
        relevance_tags=("large_tank",),
    ),
    Risk(
        name="Forsømmelse / mangel på vedlikehold",
        category="drift",
        likelihood="Høy",
        impact="Høy",
        overall="Kritisk",
        mitigation="Dobbeltbruksdesign, obligatorisk vedlikeholdsplan, inspeksjonsregime.",
        relevance_tags=("household_scale",),
    ),
    Risk(
        name="Kryssforbindelse med kommunalt nett",
        category="regelverk",
        likelihood="Lav",
        impact="Kritisk",
        overall="Høy",
        mitigation="Separat rørsystem, luftgap, regelverksetterlevelse.",
        relevance_tags=("neighbourhood_scale", "infrastructure_scale"),
    ),
    Risk(
        name="Hærverk eller manipulering (offentlige systemer)",
        category="drift",
        likelihood="Middels",
        impact="Høy",
        overall="Høy",
        mitigation="Låsbar tilgang, overvåking, synlig plassering.",
        relevance_tags=("neighbourhood_scale", "infrastructure_scale"),
    ),
    Risk(
        name="Flomforurensning av oppsamling/lagring",
        category="miljø",
        likelihood="Middels",
        impact="Høy",
        overall="Høy",
        mitigation="Hevede tankinntak, automatisk stenging ved flom.",
        relevance_tags=(),
    ),
    Risk(
        name="Atmosfærisk forurensning",
        category="miljø",
        likelihood="Lav",
        impact="Middels",
        overall="Middels",
        mitigation="First-flush-avledning, aktivt kull-behandling.",
        relevance_tags=("coastal", "industrial_area"),
    ),
    Risk(
        name="Klimaendringer reduserer pålitelighet",
        category="miljø",
        likelihood="Middels",
        impact="Middels",
        overall="Middels",
        mitigation="Design med klimamargin; revurder dimensjonering hvert 10. år.",
        relevance_tags=(),
    ),
    Risk(
        name="Brudd på regelverk",
        category="regelverk",
        likelihood="Middels",
        impact="Høy",
        overall="Høy",
        mitigation="Tidlig kontakt med Mattilsynet; følg Drikkevannsforskriften.",
        relevance_tags=("neighbourhood_scale", "infrastructure_scale"),
    ),
]


@dataclass
class CriticalControlPoint:
    id: str
    name: str
    description: str
    control_measure: str


CCPS = [
    CriticalControlPoint(
        id="CCP-1",
        name="Oppsamlingsflate",
        description="Inspeksjon og sertifisering av takmaterialer.",
        control_measure="Takbefaring, ekskludering av uegnede overflater.",
    ),
    CriticalControlPoint(
        id="CCP-2",
        name="First-flush-avledning",
        description="Verifisert automatisk avledning av de første 1-2 mm.",
        control_measure="Strømningstesting, selvresetterende mekanisme-sjekk.",
    ),
    CriticalControlPoint(
        id="CCP-3",
        name="Primærfiltrering",
        description="Integritet av sediment- og kullfilter.",
        control_measure="Turbiditetsmåling nedstrøms for filtrering.",
    ),
    CriticalControlPoint(
        id="CCP-4",
        name="Desinfeksjon",
        description="UV-intensitet eller koketemperatur/-varighet.",
        control_measure="UV-sensorlogging eller temperaturlogging; E. coli-testing.",
    ),
    CriticalControlPoint(
        id="CCP-5",
        name="Lagringstank",
        description="Mikrobiell belastning i lagret vann.",
        control_measure="Månedlig E. coli- og turbiditetstesting; årlig tankrengjøring.",
    ),
    CriticalControlPoint(
        id="CCP-6",
        name="Distribusjon",
        description="Ingen kryssforbindelse med kommunalt nett.",
        control_measure="Årlig inspeksjon av autorisert rørlegger.",
    ),
]

CATEGORY_LABELS = {
    "vannkvalitet": "Vannkvalitet",
    "infrastruktur": "Infrastruktur",
    "drift": "Drift",
    "miljø": "Miljø",
    "regelverk": "Regelverk",
}

OVERALL_SEVERITY_ORDER = {"Kritisk": 3, "Høy": 2, "Middels": 1}


SCALE_RISK_TAG = {
    "household": "household_scale",
    "neighbourhood": "neighbourhood_scale",
    "infrastructure": "infrastructure_scale",
}


def assess_scenario_risks(tank_liters, population, roof_area_m2,
                          days_tank_empty=0, longest_dry_spell=0,
                          scale=None):
    """Evaluate which risks are most relevant for a given scenario.

    Returns a list of (Risk, relevance_score, reason) tuples sorted by
    relevance_score descending. Higher score = more relevant to this scenario.

    If `scale` is provided ("household", "neighbourhood", "infrastructure"),
    risks tagged with the matching scale are boosted explicitly — this is
    more reliable than inferring scale from population or roof_area.
    """
    results = []
    explicit_scale_tag = SCALE_RISK_TAG.get(scale) if scale else None

    for risk in RISKS:
        score = OVERALL_SEVERITY_ORDER.get(risk.overall, 1)
        reasons = []

        # Scenario-specific adjustments
        if population > 0 and tank_liters > 0:
            daily_need = 13.0 * population  # WHO survival
            days_covered = tank_liters / daily_need

            if "small_tank" in risk.relevance_tags and days_covered < 14:
                score += 2
                reasons.append(f"Tanken dekker kun {days_covered:.0f} dager")

            if "high_population" in risk.relevance_tags and population > 50:
                score += 1
                reasons.append(f"Stor befolkning ({population} personer)")

            if "large_tank" in risk.relevance_tags and tank_liters > 10000:
                score += 1
                reasons.append(f"Stor tank ({tank_liters:,.0f} L) krever ekstra vedlikehold")

        if "infrastructure_scale" in risk.relevance_tags and roof_area_m2 > 500:
            score += 1
            reasons.append("Stort anlegg")

        if "neighbourhood_scale" in risk.relevance_tags and population > 20:
            score += 1
            reasons.append("Nabolagsskala")

        if "household_scale" in risk.relevance_tags and population <= 10:
            score += 1
            reasons.append("Husholdningsskala")

        if explicit_scale_tag and explicit_scale_tag in risk.relevance_tags:
            score += 2
            reasons.append(f"Relevant for valgt skala ({scale})")

        if days_tank_empty > 0 and risk.name.startswith("Langvarig"):
            score += 2
            reasons.append(f"Tanken var tom {days_tank_empty} dager i simuleringen")

        reason = "; ".join(reasons) if reasons else ""
        results.append((risk, score, reason))

    results.sort(key=lambda x: x[1], reverse=True)
    return results
