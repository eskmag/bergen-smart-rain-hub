"""Water quality: roof material risk classification and treatment barriers.

Based on docs/bergen_rainwater_emergency_supply.md §4.1 (catchment surfaces)
and §5 (multi-barrier treatment). Phase 6 ("light") scope: classification and
required-barrier lookup with NOK cost adders — no chemistry modelling.
"""

RISK_CLASSES = ("lav", "middels", "høy", "uegnet")

# Roof materials from docs §4.1. risk_class drives required treatment.
ROOF_MATERIALS = {
    "takstein": {
        "label": "Takstein (tegl/betong)",
        "risk_class": "lav",
        "description": "Uglassert tegl- eller betongtakstein. Egnet overflate.",
    },
    "metall_ny": {
        "label": "Metalltak (nyere, uten blylodding)",
        "risk_class": "lav",
        "description": "Galvanisert stål eller aluminium fra etter ca. 1980.",
    },
    "betong_forseglet": {
        "label": "Betong med matgodkjent forsegling",
        "risk_class": "lav",
        "description": "Betongtak med næringsmiddelgodkjent belegg.",
    },
    "metall_eldre": {
        "label": "Metalltak (eldre/ukjent lodding)",
        "risk_class": "middels",
        "description": "Eldre galvaniserte tak kan avgi sink; loddinger kan inneholde bly.",
    },
    "malt_tak": {
        "label": "Malt tak",
        "risk_class": "høy",
        "description": "Maling kan inneholde biocider, tungmetaller eller løsemidler.",
    },
    "shingel": {
        "label": "Shingel / takpapp (bitumen)",
        "risk_class": "høy",
        "description": "Bitumenprodukter avgir PAH-forbindelser.",
    },
    "torvtak": {
        "label": "Torv-/grønt tak",
        "risk_class": "høy",
        "description": "Høy biologisk belastning og forhøyede nitratverdier.",
    },
    "blybeslag": {
        "label": "Tak med blybeslag (typisk før 1980)",
        "risk_class": "uegnet",
        "description": "Bly løses ut i farlige konsentrasjoner. Krever utbedring før bruk.",
    },
    "kobbertak": {
        "label": "Kobbertak",
        "risk_class": "uegnet",
        "description": "Betydelig kobberutlekking, særlig i bløtt bergensvann.",
    },
}

# Required barriers per (risk_class, scale) from docs §5 + scales.py treatment
# levels. Cost adders in NOK on top of base system cost (economics.py).
_BARRIERS = {
    "lav": {
        "household": (["Førsteflush-avleder", "Sedimentfilter", "Aktivt kull",
                       "Keramisk filter"], 5_000, 15_000),
        "neighbourhood": (["Førsteflush-avleder", "Sedimentfilter", "Aktivt kull",
                           "UV-desinfeksjon"], 60_000, 200_000),
        "infrastructure": (["Førsteflush-avleder", "Sedimentfilter", "Aktivt kull",
                            "UF-membran", "UV-desinfeksjon", "Restklorering"],
                           150_000, 600_000),
    },
    "middels": {
        "household": (["Førsteflush-avleder", "Sedimentfilter", "Aktivt kull",
                       "Keramisk filter", "Metalltest årlig"], 8_000, 25_000),
        "neighbourhood": (["Førsteflush-avleder", "Sedimentfilter", "Aktivt kull",
                           "UF-membran", "UV-desinfeksjon"], 100_000, 350_000),
        "infrastructure": (["Førsteflush-avleder", "Sedimentfilter", "Aktivt kull",
                            "UF-membran", "UV-desinfeksjon", "Restklorering",
                            "Kontinuerlig overvåking"], 250_000, 900_000),
    },
    "høy": {
        "household": (["Førsteflush-avleder", "Sedimentfilter", "Aktivt kull",
                       "RO- eller UF-membran", "UV-desinfeksjon",
                       "Vannprøver hvert kvartal"], 20_000, 60_000),
        "neighbourhood": (["Førsteflush-avleder", "Sedimentfilter", "Aktivt kull",
                           "RO- eller UF-membran", "UV-desinfeksjon",
                           "Akkreditert prøvetaking"], 200_000, 700_000),
        "infrastructure": (["Takutbedring anbefales", "Førsteflush-avleder",
                            "Sedimentfilter", "Aktivt kull", "RO-membran",
                            "UV-desinfeksjon", "Restklorering",
                            "Kontinuerlig overvåking"], 500_000, 1_500_000),
    },
}


def classify_roof(material_key):
    """Return the ROOF_MATERIALS entry (KeyError on unknown key)."""
    return ROOF_MATERIALS[material_key]


def required_treatment(risk_class, scale):
    """Barriers + NOK cost adder for a risk class at a given scale.

    'uegnet' surfaces cannot be made potable by treatment alone — the
    surface itself must be remediated first (docs §4.1).
    """
    if risk_class == "uegnet":
        return {
            "potable": False,
            "barriers": [],
            "cost_low_nok": 0,
            "cost_high_nok": 0,
            "note": ("Takflaten er uegnet for drikkevann. Utbedring eller "
                     "utskifting av takmateriale kreves før oppsamling."),
        }
    barriers, low, high = _BARRIERS[risk_class][scale]
    return {
        "potable": True,
        "barriers": barriers,
        "cost_low_nok": low,
        "cost_high_nok": high,
        "note": "",
    }
