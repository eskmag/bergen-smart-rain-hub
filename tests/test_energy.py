import pytest

from backend.energy import (
    G,
    calculate_rain_energy,
    co2_offset,
    practical_equivalents,
)


# --- calculate_rain_energy ---

class TestRainEnergy:
    def test_basic(self):
        liters, energy_wh = calculate_rain_energy(10, 100, 10)
        assert liters == pytest.approx(1000.0)
        # E = mgh = 1000 * 9.81 * 10 = 98100 J = 27.25 Wh
        expected_wh = 1000 * G * 10 / 3600
        assert energy_wh == pytest.approx(expected_wh)

    def test_zero_height(self):
        _, energy_wh = calculate_rain_energy(10, 100, 0)
        assert energy_wh == 0.0

    def test_zero_rain(self):
        liters, energy_wh = calculate_rain_energy(0, 100, 10)
        assert liters == 0.0
        assert energy_wh == 0.0


# --- co2_offset ---

class TestCO2Offset:
    def test_keys(self):
        result = co2_offset(1000)
        assert "NO" in result
        assert "EU" in result

    def test_eu_higher_than_norway(self):
        result = co2_offset(1000)
        assert result["EU"] > result["NO"]


# --- practical_equivalents ---

class TestPracticalEquivalents:
    def test_keys(self):
        result = practical_equivalents(1000)
        assert set(result.keys()) == {"phone_charges", "led_bulb_hours", "laptop_charges", "electric_bike_km"}

    def test_positive(self):
        result = practical_equivalents(1000)
        assert all(v > 0 for v in result.values())
