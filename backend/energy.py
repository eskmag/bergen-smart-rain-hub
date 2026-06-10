"""Energy analysis for collected rainwater (secondary module).

Moved out of analysis.py — not exposed via any API endpoint yet.
Candidate for a future energy/visualisation page.
"""

G = 9.81  # gravitational acceleration (m/s²)

EMISSION_FACTORS = {
    "NO": 11,    # Norway: ~11 g CO₂/kWh (hydro-dominated grid)
    "EU": 250,   # EU average: ~250 g CO₂/kWh
}


def calculate_rain_energy(mm_rain, roof_area_m2, height_m):
    liters = mm_rain * roof_area_m2
    mass_kg = liters  # 1 liter water = 1 kg

    energy_joules = mass_kg * G * height_m
    energy_wh = energy_joules / 3600

    return liters, energy_wh


def co2_offset(energy_wh):
    energy_kwh = energy_wh / 1000
    return {
        grid: energy_kwh * factor
        for grid, factor in EMISSION_FACTORS.items()
    }


def practical_equivalents(energy_wh):
    return {
        "phone_charges": energy_wh / 10,
        "led_bulb_hours": energy_wh / 7,
        "laptop_charges": energy_wh / 50,
        "electric_bike_km": energy_wh / 15,
    }
