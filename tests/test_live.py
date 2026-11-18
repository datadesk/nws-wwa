"""Tests that call the real National Weather Service website.

They are skipped unless you ask for them with ``make test-live`` (or
``uv run pytest -m live``), because they are slow and fail whenever NWS is
down.
"""

import pytest

import nws_wwa

pytestmark = pytest.mark.live


@pytest.mark.parametrize(
    "func",
    [nws_wwa.get_all, nws_wwa.get_hazards, nws_wwa.get_warnings],
    ids=lambda f: f.__name__,
)
def test_live_download(func):
    """The real file downloads and reads as GeoJSON with the expected columns."""
    data = func()
    assert data["type"] == "FeatureCollection"
    for feature in data["features"]:
        assert {"CAP_ID", "PROD_TYPE", "ISSUANCE", "EXPIRATION", "URL"} <= set(
            feature["properties"]
        )
