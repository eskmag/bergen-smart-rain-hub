import pandas as pd
import pytest

from backend.analysis import (
    BERGEN_AIR_TEMP_NORMALS, BERGEN_AIR_TEMP_ANNUAL_MEAN,
    estimate_tank_temperature, tank_temperature_series,
)


class TestEstimateTankTemperature:
    def test_nedgravd_peak_in_september(self):
        # Phase peak is September → highest tank temp of the year
        temps = [estimate_tank_temperature(m, "nedgravd") for m in range(1, 13)]
        peak_month = temps.index(max(temps)) + 1
        assert peak_month == 9

    def test_nedgravd_min_in_march(self):
        temps = [estimate_tank_temperature(m, "nedgravd") for m in range(1, 13)]
        min_month = temps.index(min(temps)) + 1
        assert min_month == 3

    def test_nedgravd_amplitude_2c(self):
        temps = [estimate_tank_temperature(m, "nedgravd") for m in range(1, 13)]
        # Sinusoid amplitude is ±2°C around annual mean
        assert max(temps) - min(temps) == pytest.approx(4.0, abs=0.01)

    def test_nedgravd_centered_on_annual_mean(self):
        temps = [estimate_tank_temperature(m, "nedgravd") for m in range(1, 13)]
        assert sum(temps) / 12 == pytest.approx(BERGEN_AIR_TEMP_ANNUAL_MEAN, abs=0.05)

    def test_overflate_follows_air_temp(self):
        # Overflate model: 0.7 × air + 3
        for month, air_temp in BERGEN_AIR_TEMP_NORMALS.items():
            expected = air_temp * 0.7 + 3.0
            assert estimate_tank_temperature(month, "overflate") == pytest.approx(expected)

    def test_overflate_warmer_than_nedgravd_in_summer(self):
        # July: overflate tank gets hot, nedgravd stays cool
        ned = estimate_tank_temperature(7, "nedgravd")
        ovr = estimate_tank_temperature(7, "overflate")
        assert ovr > ned

    def test_overflate_colder_than_nedgravd_in_winter(self):
        # January: overflate freezes-adjacent, nedgravd stays moderate
        ned = estimate_tank_temperature(1, "nedgravd")
        ovr = estimate_tank_temperature(1, "overflate")
        assert ovr < ned

    def test_overflate_more_variable_than_nedgravd(self):
        ned_temps = [estimate_tank_temperature(m, "nedgravd") for m in range(1, 13)]
        ovr_temps = [estimate_tank_temperature(m, "overflate") for m in range(1, 13)]
        ned_swing = max(ned_temps) - min(ned_temps)
        ovr_swing = max(ovr_temps) - min(ovr_temps)
        assert ovr_swing > ned_swing

    def test_invalid_month_raises(self):
        with pytest.raises(ValueError):
            estimate_tank_temperature(0, "nedgravd")
        with pytest.raises(ValueError):
            estimate_tank_temperature(13, "nedgravd")

    def test_invalid_tank_type_raises(self):
        with pytest.raises(ValueError):
            estimate_tank_temperature(6, "flytende")


class TestTankTemperatureSeries:
    def _make_df(self, dates):
        return pd.DataFrame({"date": dates, "precipitation_mm": [0] * len(dates)})

    def test_length_preserved(self):
        df = self._make_df(pd.date_range("2025-01-01", periods=365, freq="D"))
        series = tank_temperature_series(df, "nedgravd")
        assert len(series) == 365

    def test_summer_warmer_than_winter_nedgravd(self):
        df = self._make_df(pd.date_range("2025-01-01", periods=365, freq="D"))
        series = tank_temperature_series(df, "nedgravd")
        # September block warmer than March block
        df["date"] = pd.to_datetime(df["date"])
        september = series[df["date"].dt.month == 9].mean()
        march = series[df["date"].dt.month == 3].mean()
        assert september > march
