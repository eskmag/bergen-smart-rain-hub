def calculate_rain_energy(mm_rain, roof_area_m2, height_m):
    liters = mm_rain * roof_area_m2
    mass_kg = liters

    g = 9.81
    energy_joules = mass_kg * g * height_m

    energy_wh = energy_joules / 3600

    return liters, energy_wh

roof_area = 100  # m2
fall_height = 5  # meter fra takrenne til bakken
rain_today = 15 # mm (en god regnværsdag i Bergen)

liter, wh = calculate_rain_energy(rain_today, roof_area, fall_height)

print(f"--- Bærekraftsrapport for taket ditt ---")
print(f"Vann samlet opp: {liter} liter")
print(f"Teoretisk energi: {wh:.2f} Wh")
print(f"Dette tilsvarer å lade en mobiltelefon ca. {wh/10:.1f} ganger.")