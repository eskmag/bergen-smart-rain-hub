from fastapi import APIRouter, HTTPException

from backend.energy import calculate_rain_energy, co2_offset, practical_equivalents
from backend.analysis import BERGEN_ANNUAL_RAINFALL_MM, DEFAULT_BUILDING_HEIGHT_M
from api.schemas import EnergyResponse

router = APIRouter()


@router.get("/energy", response_model=EnergyResponse)
def get_energy(roof_area_m2: float, height_m: float = DEFAULT_BUILDING_HEIGHT_M,
               annual_rainfall_mm: float = BERGEN_ANNUAL_RAINFALL_MM):
    if roof_area_m2 <= 0 or height_m <= 0:
        raise HTTPException(status_code=422, detail="Areal og høyde må være positive")
    liters, energy_wh = calculate_rain_energy(annual_rainfall_mm, roof_area_m2, height_m)
    return EnergyResponse(
        annual_liters=liters,
        annual_energy_kwh=energy_wh / 1000,
        co2_offset_g=co2_offset(energy_wh),
        equivalents=practical_equivalents(energy_wh),
    )
