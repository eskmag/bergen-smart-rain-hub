"""Tests for the Frost API client, with requests mocked out."""

import pandas as pd
import pytest
import requests

from backend import frost_client
from backend.frost_client import EMPTY_COLUMNS, get_rainfall_data


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def frost_payload():
    """Two days: one with precip + temp, one with temperature only."""
    return {
        "data": [
            {
                "referenceTime": "2026-06-01T00:00:00.000Z",
                "observations": [
                    {"elementId": "sum(precipitation_amount P1D)", "value": 12.4},
                    {"elementId": "mean(air_temperature P1D)", "value": 11.2},
                ],
            },
            {
                "referenceTime": "2026-06-02T00:00:00.000Z",
                "observations": [
                    {"elementId": "mean(air_temperature P1D)", "value": 9.8},
                ],
            },
        ]
    }


@pytest.fixture
def frost_env(monkeypatch):
    monkeypatch.setattr(frost_client, "FROST_API_ENDPOINT", "https://frost.test/observations")
    monkeypatch.setattr(frost_client, "FROST_CLIENT_ID", "test-id")
    monkeypatch.setattr(frost_client, "FROST_CLIENT_SECRET", "test-secret")


class TestGetRainfallData:
    def test_merges_elements_by_date(self, frost_env, monkeypatch):
        monkeypatch.setattr(
            frost_client.requests, "get", lambda *a, **kw: FakeResponse(frost_payload())
        )
        df = get_rainfall_data(days=2)
        assert list(df.columns) == EMPTY_COLUMNS
        # the temperature-only day is dropped (DB requires NOT NULL precipitation)
        assert len(df) == 1
        row = df.iloc[0]
        assert row["date"] == "2026-06-01"
        assert row["precipitation_mm"] == 12.4
        assert row["air_temperature_c"] == 11.2

    def test_uses_default_station(self, frost_env, monkeypatch):
        captured = {}

        def fake_get(url, params=None, **kw):
            captured["params"] = params
            return FakeResponse(frost_payload())

        monkeypatch.setattr(frost_client.requests, "get", fake_get)
        df = get_rainfall_data(days=2)
        assert captured["params"]["sources"] == frost_client.DEFAULT_STATION_ID
        assert (df["station_id"] == frost_client.DEFAULT_STATION_ID).all()

    def test_request_error_returns_empty_frame(self, frost_env, monkeypatch):
        def fake_get(*a, **kw):
            raise requests.ConnectionError("boom")

        monkeypatch.setattr(frost_client.requests, "get", fake_get)
        df = get_rainfall_data(days=2)
        assert df.empty
        assert list(df.columns) == EMPTY_COLUMNS

    def test_missing_credentials_returns_empty_frame(self, monkeypatch):
        monkeypatch.setattr(frost_client, "FROST_API_ENDPOINT", "")
        df = get_rainfall_data(days=2)
        assert df.empty
        assert list(df.columns) == EMPTY_COLUMNS

    def test_no_data_returns_empty_frame(self, frost_env, monkeypatch):
        monkeypatch.setattr(
            frost_client.requests, "get", lambda *a, **kw: FakeResponse({"data": []})
        )
        df = get_rainfall_data(days=2)
        assert df.empty
        assert isinstance(df, pd.DataFrame)
