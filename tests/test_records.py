"""Offline tests of the typed alert records."""

import dataclasses
import doctest
from datetime import UTC, datetime

import pytest

import nws_wwa
from nws_wwa import Alert, Feed, options, records


def test_records_doctests():
    """The examples in the records and options docstrings are correct."""
    assert doctest.testmod(records).failed == 0
    assert doctest.testmod(options).failed == 0


def test_records_match_the_geojson(fake_nws):
    """The records and the GeoJSON describe the same alerts in the same order."""
    data = nws_wwa.get_all()
    found = nws_wwa.get_alert_records("all")
    assert len(found) == len(data["features"]) == 7
    for alert, feature in zip(found, data["features"], strict=True):
        assert alert.cap_id == feature["properties"]["CAP_ID"]
        assert alert.product_type == feature["properties"]["PROD_TYPE"]
        assert alert.url == feature["properties"]["URL"]
        assert alert.geometry["type"] == feature["geometry"]["type"]
        assert type(alert.geometry) is dict


def test_each_feed_has_its_own_file(fake_nws):
    """Each short name downloads its own file, and the enum works the same way."""
    assert len(nws_wwa.get_alert_records(Feed.HAZARDS)) == 6
    assert len(nws_wwa.get_alert_records("warnings")) == 1
    assert fake_nws.urls[0].endswith("/current_hazards.tar.gz")
    assert fake_nws.urls[1].endswith("/current_warnings.tar.gz")
    with pytest.raises(ValueError):
        nws_wwa.get_alert_records("everything")


def test_warning_record(fake_nws):
    """The one real warning in the sample has parsed numbers and UTC times."""
    (alert,) = nws_wwa.get_alert_records("warnings")
    assert alert.product_type == "Special Marine Warning"
    assert alert.message_type == "SMW"
    assert alert.phenomenon == "MA"
    assert alert.significance == "W"
    assert alert.significance_name == "Warning"
    assert alert.office == "KMFL"
    assert alert.event_number == 365
    assert alert.issued_at == datetime(2026, 11, 18, 15, 3, tzinfo=UTC)
    assert alert.expires_at == datetime(2026, 11, 18, 16, 30, tzinfo=UTC)
    assert alert.ends_at == alert.expires_at
    assert alert.issued_at.tzinfo is UTC
    assert alert.vtec == "/O.NEW.KMFL.MA.W.0365.261118T1503Z-261118T1630Z/"
    assert alert.geometry["type"] == "Polygon"


def test_statement_has_empty_codes(fake_nws):
    """Statements have no VTEC code, so those fields are None rather than empty text."""
    statements = [a for a in nws_wwa.get_alert_records("all") if a.vtec is None]
    assert statements
    for alert in statements:
        assert alert.phenomenon is None
        assert alert.significance is None
        assert alert.significance_name is None
        assert alert.office is None
        assert alert.event_number is None


def test_all_the_kinds_in_the_sample(fake_nws):
    """The sample holds warnings, watches, advisories and multipolygons."""
    found = nws_wwa.get_alert_records("all")
    assert {a.significance_name for a in found} >= {"Warning", "Watch", "Advisory"}
    assert "MultiPolygon" in {a.geometry["type"] for a in found}


def test_every_time_has_a_timezone(fake_nws):
    """Every time in every record is timezone-aware UTC."""
    for alert in nws_wwa.get_alert_records("all"):
        for value in (alert.issued_at, alert.expires_at, alert.onset_at):
            assert value is not None
            assert value.utcoffset().total_seconds() == 0


def test_records_are_frozen(fake_nws):
    """A record cannot be changed after it is made."""
    (alert,) = nws_wwa.get_alert_records("warnings")
    with pytest.raises(dataclasses.FrozenInstanceError):
        alert.office = "KXXX"  # type: ignore[misc]


def test_unknown_significance_is_kept():
    """A new one-letter code from NWS is passed through, not hidden."""
    feature = _feature(SIG="Z")
    assert Alert.from_feature(feature).significance_name == "Z"


def _feature(**changes):
    """Make a feature like NWS's, with some values replaced."""
    properties = {
        "CAP_ID": "urn:oid:1",
        "MSG_TYPE": "FFW",
        "PROD_TYPE": "Flash Flood Warning",
        "VTEC": "/O.NEW.KMFL.FF.W.0019.000000T0000Z-261118T0700Z/",
        "PHENOM": "FF",
        "SIG": "W",
        "WFO": "KMFL",
        "EVENT": "0019",
        "ISSUANCE": "2026-11-18T00:42:00-05:00",
        "EXPIRATION": "2026-11-18T02:00:00-05:00",
        "ONSET": "2026-11-18T00:42:00-05:00",
        "ENDS": None,
        "URL": "https://api.weather.gov/alerts/urn:oid:1",
    }
    properties.update(changes)
    return {"geometry": None, "properties": properties}


def test_missing_ends_is_none():
    """An alert with no end time has ends_at of None."""
    assert Alert.from_feature(_feature()).ends_at is None


@pytest.mark.parametrize(
    "changes,message",
    [
        ({"ISSUANCE": None}, "ISSUANCE"),
        ({"EXPIRATION": "soon"}, "not a time"),
        ({"ONSET": "2026-11-18T00:42:00"}, "no time zone"),
        ({"EVENT": "abc"}, "not a number"),
    ],
)
def test_unreadable_values_raise_value_error(changes, message):
    """A value that cannot be read raises a ValueError that says which one."""
    with pytest.raises(ValueError, match=message):
        Alert.from_feature(_feature(**changes))


def test_missing_column_raises_value_error():
    """A feature without a required column raises a ValueError naming it."""
    feature = _feature()
    del feature["properties"]["CAP_ID"]
    with pytest.raises(ValueError, match="CAP_ID"):
        Alert.from_feature(feature)
