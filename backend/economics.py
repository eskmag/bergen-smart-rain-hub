"""Economic analysis for rainwater harvesting systems.

Cost data from docs/bergen_rainwater_emergency_supply.md, section 14.
All costs in NOK.
"""

from dataclasses import dataclass


@dataclass
class CostEstimate:
    label: str
    capital_low: int
    capital_high: int
    annual_operating_low: int
    annual_operating_high: int
    capacity_low: int
    capacity_high: int


COST_ESTIMATES = [
    CostEstimate("Enebolig / husholdning", 15_000, 45_000, 1_500, 3_000, 4, 6),
    CostEstimate("Boligblokk (20 enheter)", 80_000, 200_000, 5_000, 12_000, 40, 60),
    CostEstimate("Nabolag (500 beboere)", 800_000, 2_500_000, 40_000, 100_000, 400, 600),
    CostEstimate("Skole / offentlig bygg", 500_000, 1_500_000, 30_000, 80_000, 200, 500),
    CostEstimate("Sykehusavdeling", 2_000_000, 8_000_000, 150_000, 400_000, 500, 2_000),
]

CAPITAL_CATEGORIES = [
    ("Kartlegging og utbedring av tak", 0.10),
    ("Tank (levering og installasjon)", 0.30),
    ("First-flush og takrenner", 0.10),
    ("Behandlingsutstyr", 0.20),
    ("Rør og distribusjon", 0.15),
    ("Prosjektledelse og prosjektering", 0.10),
    ("Godkjenning og sertifisering", 0.05),
]

OPERATING_CATEGORIES = [
    ("Filterkassetter (årlig)", 0.25),
    ("Vannkvalitetstesting", 0.20),
    ("Tankrengjøring (årlig)", 0.15),
    ("Vedlikeholdsarbeid", 0.25),
    ("Rapportering og tilsyn", 0.10),
    ("Energi", 0.05),
]


def find_best_estimate(population):
    """Find the cost estimate tier that best matches the given population."""
    for est in COST_ESTIMATES:
        if est.capacity_low <= population <= est.capacity_high:
            return est
    # If population exceeds all tiers, use the largest; if below, use smallest
    if population < COST_ESTIMATES[0].capacity_low:
        return COST_ESTIMATES[0]
    return COST_ESTIMATES[-1]


def interpolate_cost(population, est):
    """Interpolate within a cost estimate tier based on population.

    Returns (capital, annual_operating) as midpoint-weighted estimates.
    """
    if est.capacity_high == est.capacity_low:
        ratio = 0.5
    else:
        ratio = (population - est.capacity_low) / (est.capacity_high - est.capacity_low)
        ratio = max(0.0, min(1.0, ratio))

    capital = est.capital_low + ratio * (est.capital_high - est.capital_low)
    operating = est.annual_operating_low + ratio * (est.annual_operating_high - est.annual_operating_low)

    return round(capital), round(operating)


def lifecycle_cost(capital, annual_operating, years):
    """Total cost over a given number of years (no discounting)."""
    return capital + annual_operating * years


def cost_per_person(total_cost, population):
    """Cost per person served."""
    if population <= 0:
        return 0
    return total_cost / population


def cost_per_liter(total_cost, annual_liters, years):
    """Cost per liter of water collected over the system lifetime."""
    total_liters = annual_liters * years
    if total_liters <= 0:
        return 0
    return total_cost / total_liters


def cost_breakdown(total_amount, categories):
    """Break a total amount into category shares.

    Returns list of (category_name, amount) tuples.
    """
    return [(name, round(total_amount * share)) for name, share in categories]
