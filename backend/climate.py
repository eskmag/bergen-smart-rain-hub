"""Climate projection adjustments for precipitation data.

Based on docs/bergen_rainwater_emergency_supply.md, section 3.4.
Applies synthetic adjustments to historical data rather than fetching
projected climate data, as recommended in the framework (15-20% margins).
"""

import pandas as pd
import numpy as np

SCENARIOS = {
    "historical": {
        "label": "Historisk (ingen endring)",
        "intensity_factor": 1.0,
        "dry_spell_factor": 1.0,
        "description": "Bruker historiske data uten justeringer.",
    },
    "moderate": {
        "label": "Moderat klimaendring",
        "intensity_factor": 1.10,  # +10% intensity on rainy days
        "dry_spell_factor": 1.15,  # +15% longer dry spells
        "description": "Basert på norske klimafremskrivninger: +10 % nedbørsintensitet, "
                       "+15 % lengre tørkeperioder. Representerer et middels scenario.",
    },
    "pessimistic": {
        "label": "Pessimistisk klimaendring",
        "intensity_factor": 1.20,  # +20% intensity on rainy days
        "dry_spell_factor": 1.25,  # +25% longer dry spells
        "description": "Konservativt scenario: +20 % nedbørsintensitet, "
                       "+25 % lengre tørkeperioder. Anbefalt for kritisk infrastruktur.",
    },
}


def apply_climate_projection(df, scenario="moderate"):
    """Apply climate adjustment factors to precipitation data.

    - Rainy days (>=1mm): multiply precipitation by intensity_factor
    - Dry days (<1mm): extend dry spells by converting some rainy days at
      spell boundaries to dry days, proportional to dry_spell_factor

    Returns a new DataFrame with adjusted precipitation values.
    """
    if scenario == "historical":
        return df.copy()

    params = SCENARIOS[scenario]
    intensity_factor = params["intensity_factor"]
    dry_spell_factor = params["dry_spell_factor"]

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["precipitation_mm"] = df["precipitation_mm"].astype(float)
    df = df.sort_values("date").reset_index(drop=True)

    # Step 1: Increase intensity on rainy days
    rainy_mask = df["precipitation_mm"] >= 1.0
    df.loc[rainy_mask, "precipitation_mm"] = (
        df.loc[rainy_mask, "precipitation_mm"] * intensity_factor
    )

    # Step 2: Extend dry spells by converting light-rain days at spell edges to dry
    # Identify dry spells (< 1mm)
    df["dry"] = df["precipitation_mm"] < 1.0
    df["spell_id"] = (~df["dry"]).cumsum()

    extension_ratio = dry_spell_factor - 1.0  # e.g., 0.15 for moderate

    for spell_id, group in df[df["dry"]].groupby("spell_id"):
        spell_len = len(group)
        extend_by = max(1, round(spell_len * extension_ratio))

        # Find the day after the spell ends
        last_idx = group.index[-1]
        for i in range(1, extend_by + 1):
            target_idx = last_idx + i
            if target_idx < len(df) and df.loc[target_idx, "precipitation_mm"] < 5.0:
                # Only convert light rain days, not heavy rain days
                df.loc[target_idx, "precipitation_mm"] = 0.0

    df = df.drop(columns=["dry", "spell_id"])
    return df


def compare_scenarios(df, scenarios=None):
    """Apply multiple climate scenarios and return summary statistics.

    Returns a list of dicts with scenario name, total precipitation,
    dry days count, and longest dry spell.
    """
    if scenarios is None:
        scenarios = list(SCENARIOS.keys())

    results = []
    for scenario_key in scenarios:
        adjusted = apply_climate_projection(df, scenario_key)
        params = SCENARIOS[scenario_key]

        total_precip = adjusted["precipitation_mm"].sum()
        dry_days = (adjusted["precipitation_mm"] < 1.0).sum()

        # Calculate longest dry spell
        adjusted_sorted = adjusted.sort_values("date")
        is_dry = adjusted_sorted["precipitation_mm"] < 1.0
        spell_groups = (~is_dry).cumsum()
        dry_spells = is_dry.groupby(spell_groups).sum()
        longest_dry = int(dry_spells.max()) if not dry_spells.empty else 0

        results.append({
            "scenario": scenario_key,
            "label": params["label"],
            "total_precip_mm": round(total_precip, 1),
            "dry_days": int(dry_days),
            "longest_dry_spell": longest_dry,
        })

    return results
