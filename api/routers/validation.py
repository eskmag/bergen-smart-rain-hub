from fastapi import APIRouter, HTTPException

from scripts.backtest_2018 import backtest_2018
from api.schemas import ValidationResponse

router = APIRouter()


@router.get("/validation", response_model=ValidationResponse)
def get_validation():
    """2018 dry-spring backtest against measured SN50540 data.

    Returns 503 if the DB holds no 2018 observations (e.g. a fresh clone
    before running the pipeline) so the frontend can degrade gracefully.
    """
    try:
        return backtest_2018()
    except ValueError as exc:
        raise HTTPException(status_code=503, detail="Valideringsdata ikke tilgjengelig") from exc
