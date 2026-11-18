"""Offline tests of the download functions, using saved samples of real NWS data."""

import pytest

import nws_wwa

PROPERTY_NAMES = {
    "CAP_ID",
    "MSG_TYPE",
    "PROD_TYPE",
    "VTEC",
    "PHENOM",
    "SIG",
    "WFO",
    "EVENT",
    "ISSUANCE",
    "EXPIRATION",
    "ONSET",
    "ENDS",
    "URL",
}


@pytest.mark.parametrize(
    "func,name,count",
    [
        (nws_wwa.get_all, "current_all", 7),
        (nws_wwa.get_hazards, "current_hazards", 6),
        (nws_wwa.get_warnings, "current_warnings", 1),
    ],
)
def test_download(fake_nws, func, name, count):
    """Each function asks NWS for its own file and returns GeoJSON features."""
    data = func()
    assert fake_nws.urls == [
        f"https://tgftp.nws.noaa.gov/SL.us008001/DF.sha/DC.cap/DS.WWA/{name}.tar.gz"
    ]
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == count
    for feature in data["features"]:
        assert feature["type"] == "Feature"
        assert set(feature["properties"]) == PROPERTY_NAMES
        assert feature["geometry"]["type"] in {"Polygon", "MultiPolygon"}


def test_values_are_kept_as_published(fake_nws):
    """Times stay as NWS text and statements keep their empty values."""
    data = nws_wwa.get_all()
    properties = [f["properties"] for f in data["features"]]
    assert all(len(p["ISSUANCE"]) == 25 for p in properties)
    statement = [p for p in properties if p["VTEC"] is None]
    assert statement
    assert all(p["SIG"] is None and p["WFO"] is None for p in statement)
    assert all(
        p["URL"].startswith("https://api.weather.gov/alerts/") for p in properties
    )
