from fastapi import APIRouter, HTTPException

from backend.bydel import city_potential
from api.schemas import BydelResponse

router = APIRouter()


@router.get("/bydel", response_model=BydelResponse)
def get_bydel(participation: float = 0.20):
    try:
        result = city_potential(participation_pct=participation)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return BydelResponse(**result)
