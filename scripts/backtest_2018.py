"""CLI for the 2018 dry-spring backtest — human-readable printout.

    python scripts/backtest_2018.py

The computation itself lives in `backend/backtest.py` (pure logic belongs in
`backend/`, and `scripts/` is not a packaged module — importing it from the API
broke the Docker image, which only ships the declared packages).
"""

from backend.backtest import backtest_2018


def _print_summary(result):
    ls = result["longest_dry_spell"]
    print(f"Backtest {result['year']} — stasjon {result['station_id']}")
    print(f"  Total nedbør:        {result['total_rainfall_mm']:.0f} mm")
    print(f"  Tørkeperioder (≥3d): {result['n_dry_spells']}")
    print(f"  Lengste tørkeperiode: {ls['days']} dager  {ls['start']} → {ls['end']}")
    c = result["case"]
    print(f"  Case: enebolig {c['roof_m2']} m², {c['population']} personer, "
          f"virkningsgrad {c['efficiency']:.0%}")
    for t in result["tiers"]:
        print(f"    {t['label']:9s} ({t['liters']:5d} L): "
              f"dager tom tank = {t['days_tank_empty']}, "
              f"min tanknivå = {t['min_tank_liters']} L")


if __name__ == "__main__":
    _print_summary(backtest_2018())
