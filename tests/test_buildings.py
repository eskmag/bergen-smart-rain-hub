import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend import buildings


# A square roughly 20 m on a side, with the lookup point inside it.
INSIDE = [
    {"lat": 60.3890, "lon": 5.3260},
    {"lat": 60.3890, "lon": 5.3264},
    {"lat": 60.3894, "lon": 5.3264},
    {"lat": 60.3894, "lon": 5.3260},
]
# A neighbour that does not contain the point.
ELSEWHERE = [
    {"lat": 60.3900, "lon": 5.3280},
    {"lat": 60.3900, "lon": 5.3284},
    {"lat": 60.3904, "lon": 5.3284},
    {"lat": 60.3904, "lon": 5.3280},
]

POINT = (60.3892, 5.3262)


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {"elements": []}

    def json(self):
        return self._payload


@pytest.fixture(autouse=True)
def clear_cache():
    buildings.clear_cache()
    yield
    buildings.clear_cache()


def elements(*rings):
    return {"elements": [{"type": "way", "geometry": list(r)} for r in rings]}


class TestFootprintLookup:
    def test_returns_polygon_containing_the_point(self, monkeypatch):
        monkeypatch.setattr(
            buildings, "_post",
            lambda url, query: FakeResponse(payload=elements(ELSEWHERE, INSIDE)),
        )
        geom = buildings.footprint_for(*POINT)
        assert geom["type"] == "Polygon"
        ring = geom["coordinates"][0]
        # GeoJSON is lon/lat, and the ring must be closed.
        assert ring[0] == [5.3260, 60.3890]
        assert ring[0] == ring[-1]

    def test_prefers_containing_polygon_over_first_hit(self, monkeypatch):
        monkeypatch.setattr(
            buildings, "_post",
            lambda url, query: FakeResponse(payload=elements(ELSEWHERE, INSIDE)),
        )
        geom = buildings.footprint_for(*POINT)
        assert [5.3260, 60.3890] in geom["coordinates"][0]

    def test_returns_none_when_no_buildings(self, monkeypatch):
        monkeypatch.setattr(
            buildings, "_post", lambda url, query: FakeResponse(payload={"elements": []})
        )
        assert buildings.footprint_for(*POINT) is None


class TestRetryPolicy:
    def test_retries_transient_5xx_then_succeeds(self, monkeypatch):
        calls = []

        def fake_post(url, query):
            calls.append(url)
            if len(calls) == 1:
                return FakeResponse(status_code=504)
            return FakeResponse(payload=elements(INSIDE))

        monkeypatch.setattr(buildings, "_post", fake_post)
        monkeypatch.setattr(buildings.time, "sleep", lambda s: None)
        assert buildings.footprint_for(*POINT) is not None
        assert len(calls) == 2

    def test_does_not_retry_when_told_to_back_off(self, monkeypatch):
        # 406/429 is the server declining, not transient load. Retrying it is
        # exactly the hammering the block exists to stop.
        for status in (406, 429):
            buildings.clear_cache()
            calls = []

            def fake_post(url, query, _s=status):
                calls.append(url)
                return FakeResponse(status_code=_s)

            monkeypatch.setattr(buildings, "_post", fake_post)
            monkeypatch.setattr(buildings.time, "sleep", lambda s: None)
            with pytest.raises(buildings.FootprintUnavailable):
                buildings.footprint_for(*POINT)
            # One attempt per endpoint, no retries within an endpoint.
            assert len(calls) == len(buildings.OVERPASS_ENDPOINTS)

    def test_raises_when_every_endpoint_fails(self, monkeypatch):
        monkeypatch.setattr(
            buildings, "_post", lambda url, query: FakeResponse(status_code=504)
        )
        monkeypatch.setattr(buildings.time, "sleep", lambda s: None)
        with pytest.raises(buildings.FootprintUnavailable):
            buildings.footprint_for(*POINT)

    def test_network_error_is_retried(self, monkeypatch):
        calls = []

        def fake_post(url, query):
            calls.append(url)
            if len(calls) == 1:
                raise requests.RequestException("boom")
            return FakeResponse(payload=elements(INSIDE))

        monkeypatch.setattr(buildings, "_post", fake_post)
        monkeypatch.setattr(buildings.time, "sleep", lambda s: None)
        assert buildings.footprint_for(*POINT) is not None


class TestCaching:
    def test_repeat_lookup_does_not_hit_the_network(self, monkeypatch):
        calls = []

        def fake_post(url, query):
            calls.append(url)
            return FakeResponse(payload=elements(INSIDE))

        monkeypatch.setattr(buildings, "_post", fake_post)
        buildings.footprint_for(*POINT)
        buildings.footprint_for(*POINT)
        assert len(calls) == 1

    def test_misses_are_cached_too(self, monkeypatch):
        # "No building here" is a stable answer — re-asking Overpass for it
        # burns quota against a free endpoint for nothing.
        calls = []

        def fake_post(url, query):
            calls.append(url)
            return FakeResponse(payload={"elements": []})

        monkeypatch.setattr(buildings, "_post", fake_post)
        assert buildings.footprint_for(*POINT) is None
        assert buildings.footprint_for(*POINT) is None
        assert len(calls) == 1

    def test_nearby_points_share_a_cache_entry(self, monkeypatch):
        calls = []

        def fake_post(url, query):
            calls.append(url)
            return FakeResponse(payload=elements(INSIDE))

        monkeypatch.setattr(buildings, "_post", fake_post)
        buildings.footprint_for(60.38920, 5.32620)
        buildings.footprint_for(60.389201, 5.326201)
        assert len(calls) == 1


class TestPolicyCompliance:
    def test_sends_an_identifying_user_agent(self, monkeypatch):
        seen = {}

        def fake_requests_post(url, data=None, headers=None, timeout=None):
            seen["headers"] = headers or {}
            return FakeResponse(payload=elements(INSIDE))

        monkeypatch.setattr(buildings.requests, "post", fake_requests_post)
        buildings.footprint_for(*POINT)
        ua = seen["headers"].get("User-Agent", "")
        # OSM's policy requires identifying the application, and explicitly
        # warns that impersonating another app gets you blocked.
        assert "BergenSmartRainHub" in ua
        assert "Mozilla" not in ua
