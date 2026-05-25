from fastapi import APIRouter

from backend.risk import CCPS, CATEGORY_LABELS, assess_scenario_risks
from api.schemas import RiskAssessRequest, RiskAssessResponse, AssessedRisk, CCP

router = APIRouter()


@router.post("/assess/risk", response_model=RiskAssessResponse)
def assess_risk(req: RiskAssessRequest):
    assessed = assess_scenario_risks(
        tank_liters=req.tank_liters,
        population=req.population,
        roof_area_m2=req.roof_area_m2,
        days_tank_empty=req.days_tank_empty,
        longest_dry_spell=req.longest_dry_spell,
        scale=req.scale,
    )

    return RiskAssessResponse(
        assessed_risks=[
            AssessedRisk(
                name=risk.name,
                category=risk.category,
                likelihood=risk.likelihood,
                impact=risk.impact,
                overall=risk.overall,
                mitigation=risk.mitigation,
                score=score,
                reason=reason,
            )
            for risk, score, reason in assessed
        ],
        ccps=[
            CCP(
                id=ccp.id,
                name=ccp.name,
                description=ccp.description,
                control_measure=ccp.control_measure,
            )
            for ccp in CCPS
        ],
        category_labels=CATEGORY_LABELS,
    )
