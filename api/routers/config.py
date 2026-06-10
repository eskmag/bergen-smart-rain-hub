from fastapi import APIRouter

from backend.analysis import BUILDING_PRESETS, WATER_NEEDS
from backend.climate import SCENARIOS
from backend.scales import SCALES, SCALE_PRESETS, INFRASTRUCTURE_FACILITIES
from api.schemas import (
    ConfigResponse, ConfigDefaults, ScaleSchema, BuildingPreset,
    InfrastructureFacility, ClimateScenario,
)

router = APIRouter()


@router.get("/config", response_model=ConfigResponse)
def get_config():
    scales = [
        ScaleSchema(
            key=s.key,
            label=s.label,
            description=s.description,
            typical_population=list(s.typical_population),
            typical_tank_liters=list(s.typical_tank_liters),
            typical_buildings=list(s.typical_buildings),
            treatment_level=s.treatment_level,
            governance_note=s.governance_note,
            cost_range_nok=list(s.cost_range_nok),
        )
        for s in SCALES.values()
    ]

    building_presets = [
        BuildingPreset(key=k, **v)
        for k, v in BUILDING_PRESETS.items()
    ]

    infrastructure_facilities = [
        InfrastructureFacility(key=k, **v)
        for k, v in INFRASTRUCTURE_FACILITIES.items()
    ]

    climate_scenarios = [
        ClimateScenario(key=k, **v)
        for k, v in SCENARIOS.items()
    ]

    return ConfigResponse(
        scales=scales,
        scale_presets=SCALE_PRESETS,
        building_presets=building_presets,
        infrastructure_facilities=infrastructure_facilities,
        climate_scenarios=climate_scenarios,
        water_needs=WATER_NEEDS,
        defaults=ConfigDefaults(),
    )
