from fastapi import APIRouter, HTTPException

from backend.treatment import ROOF_MATERIALS, classify_roof, required_treatment
from api.schemas import TreatmentResponse

router = APIRouter()


@router.get("/treatment", response_model=TreatmentResponse)
def get_treatment(material: str, scale: str = "household"):
    if material not in ROOF_MATERIALS:
        raise HTTPException(status_code=422, detail=f"Ukjent takmateriale: {material!r}")
    mat = classify_roof(material)
    try:
        t = required_treatment(mat["risk_class"], scale)
    except KeyError:
        raise HTTPException(status_code=422, detail=f"Ukjent skala: {scale!r}")
    return TreatmentResponse(
        material=material,
        material_label=mat["label"],
        risk_class=mat["risk_class"],
        **t,
    )
