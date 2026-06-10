from fastapi import APIRouter, HTTPException, Query

from backend.economics import (
    COST_ESTIMATES, CAPITAL_CATEGORIES, OPERATING_CATEGORIES,
    choose_estimate, interpolate_cost,
    lifecycle_cost, cost_per_person, cost_per_liter, cost_breakdown,
)
from api.schemas import CostsResponse, CostEstimateRow, CostBreakdownItem

router = APIRouter()


@router.get("/costs", response_model=CostsResponse)
def get_costs(
    population: int = Query(ge=1),
    scale: str = Query(default="household"),
    annual_liters: float = Query(default=0, ge=0),
):
    try:
        est = choose_estimate(scale, population)
    except KeyError:
        raise HTTPException(status_code=422, detail=f"Ukjent skala: {scale!r}")

    capital, annual_op = interpolate_cost(population, est)

    cpl_20 = (
        cost_per_liter(lifecycle_cost(capital, annual_op, 20), annual_liters, 20)
        if annual_liters > 0 else None
    )

    cap_breakdown = cost_breakdown(capital, CAPITAL_CATEGORIES)
    op_breakdown = cost_breakdown(annual_op, OPERATING_CATEGORIES)

    return CostsResponse(
        estimate_label=est.label,
        capital_low=est.capital_low,
        capital_high=est.capital_high,
        annual_op_low=est.annual_operating_low,
        annual_op_high=est.annual_operating_high,
        capital=capital,
        annual_op=annual_op,
        cost_per_person=cost_per_person(capital, population),
        lifecycle_10=lifecycle_cost(capital, annual_op, 10),
        lifecycle_20=lifecycle_cost(capital, annual_op, 20),
        lifecycle_30=lifecycle_cost(capital, annual_op, 30),
        cost_per_liter_20=cpl_20,
        capital_breakdown=[CostBreakdownItem(category=c, amount=a) for c, a in cap_breakdown],
        operating_breakdown=[CostBreakdownItem(category=c, amount=a) for c, a in op_breakdown],
        all_estimates=[
            CostEstimateRow(
                label=e.label,
                capital_low=e.capital_low,
                capital_high=e.capital_high,
                annual_operating_low=e.annual_operating_low,
                annual_operating_high=e.annual_operating_high,
                capacity_low=e.capacity_low,
                capacity_high=e.capacity_high,
            )
            for e in COST_ESTIMATES
        ],
    )
