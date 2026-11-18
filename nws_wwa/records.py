"""Typed records for the alerts the National Weather Service publishes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

SIGNIFICANCE_NAMES = {
    "W": "Warning",
    "A": "Watch",
    "Y": "Advisory",
    "S": "Statement",
    "F": "Forecast",
    "O": "Outlook",
    "N": "Synopsis",
}
"""What each one-letter ``significance`` code means in NWS's VTEC system."""


def _parse_time(value: Any, name: str) -> datetime:
    """Read one of NWS's time strings as a timezone-aware UTC time.

    NWS writes times in the local time of the forecast office, with the offset
    at the end, such as "2026-11-18T07:43:00-08:00".

    Args:
        value: The text from NWS.
        name: The NWS column name, used in the error message.

    Returns:
        The same moment, as a ``datetime`` in UTC.

    Raises:
        ValueError: If the text is missing, is not a time, or has no offset.

    Examples:
        >>> _parse_time("2026-11-18T07:43:00-08:00", "ISSUANCE")
        datetime.datetime(2026, 11, 18, 15, 43, tzinfo=datetime.timezone.utc)
    """
    if not isinstance(value, str) or not value:
        raise ValueError(f"NWS's alert has no {name} time")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"NWS's {name} value {value!r} is not a time") from error
    if parsed.tzinfo is None:
        raise ValueError(f"NWS's {name} value {value!r} has no time zone")
    return parsed.astimezone(UTC)


def _optional_time(value: Any, name: str) -> datetime | None:
    """Read a time that NWS may leave empty.

    Args:
        value: The text from NWS, or None.
        name: The NWS column name, used in the error message.

    Returns:
        A UTC ``datetime``, or None when NWS left it empty.

    Raises:
        ValueError: If there is text and it is not a time with an offset.

    Examples:
        >>> _optional_time(None, "ENDS") is None
        True
    """
    if value is None or value == "":
        return None
    return _parse_time(value, name)


def _optional_text(value: Any) -> str | None:
    """Turn an empty value into None and anything else into text.

    Args:
        value: The value from NWS.

    Returns:
        The text, or None when it was empty.

    Examples:
        >>> _optional_text("") is None
        True
        >>> _optional_text("FA")
        'FA'
    """
    if value is None or value == "":
        return None
    return str(value)


@dataclass(frozen=True, slots=True)
class Alert:
    """One watch, warning, advisory or statement area from the National Weather Service.

    This is a copy of what NWS published. It is not an official alert. For
    anything that affects safety, read the alert on weather.gov. Each record is
    one row of NWS's file, with one shape. The same alert can have more than
    one row, so count alerts by ``cap_id`` or ``vtec``, not by records.

    Statements and a few other products have no VTEC code, so ``vtec``,
    ``phenomenon``, ``significance``, ``office`` and ``event_number`` can be
    None.

    Attributes:
        cap_id: NWS's unique identifier for the alert, in the Common Alerting
            Protocol (CAP) format.
        message_type: The three-letter product code of the text bulletin, such
            as "FFW" or "SMW".
        product_type: The name of the product in words, such as "Flash Flood
            Warning".
        vtec: The full Valid Time Event Code, which NWS uses to track an event
            from its first message to its end.
        phenomenon: The two-letter code for the kind of weather, such as "FF"
            for flash flood.
        significance: The one-letter code for how serious it is, such as "W"
            for warning, "A" for watch or "Y" for advisory.
        office: The four-letter code of the NWS forecast office that issued it.
        event_number: The office's running number for this event this year.
        issued_at: When NWS issued the message, in UTC.
        expires_at: When the message expires, in UTC.
        onset_at: When the hazard is expected to begin, in UTC.
        ends_at: When the hazard is expected to end, in UTC, or None.
        url: The address of the alert in the NWS API.
        geometry: The area of the alert as a GeoJSON polygon or multipolygon,
            as a plain dictionary.

    Examples:
        >>> feature = {
        ...     "geometry": {"type": "Polygon", "coordinates": []},
        ...     "properties": {
        ...         "CAP_ID": "urn:oid:1",
        ...         "MSG_TYPE": "FFW",
        ...         "PROD_TYPE": "Flash Flood Warning",
        ...         "VTEC": "/O.NEW.KMFL.FF.W.0019.000000T0000Z-261118T0700Z/",
        ...         "PHENOM": "FF",
        ...         "SIG": "W",
        ...         "WFO": "KMFL",
        ...         "EVENT": "0019",
        ...         "ISSUANCE": "2026-11-18T00:42:00-05:00",
        ...         "EXPIRATION": "2026-11-18T02:00:00-05:00",
        ...         "ONSET": "2026-11-18T00:42:00-05:00",
        ...         "ENDS": "2026-11-18T02:00:00-05:00",
        ...         "URL": "https://api.weather.gov/alerts/urn:oid:1",
        ...     },
        ... }
        >>> alert = Alert.from_feature(feature)
        >>> alert.issued_at.isoformat()
        '2026-11-18T05:42:00+00:00'
        >>> alert.event_number
        19
        >>> alert.significance_name
        'Warning'
    """

    cap_id: str
    message_type: str
    product_type: str
    vtec: str | None
    phenomenon: str | None
    significance: str | None
    office: str | None
    event_number: int | None
    issued_at: datetime
    expires_at: datetime
    onset_at: datetime | None
    ends_at: datetime | None
    url: str
    geometry: dict[str, Any]

    @property
    def significance_name(self) -> str | None:
        """The significance code in words.

        Returns:
            "Warning", "Watch", "Advisory" and so on, the code itself if NWS
            adds a letter this package does not know, or None when the alert
            has no significance.

        Examples:
            >>> Alert.from_feature(_EXAMPLE).significance_name
            'Advisory'
        """
        if self.significance is None:
            return None
        return SIGNIFICANCE_NAMES.get(self.significance, self.significance)

    @classmethod
    def from_feature(cls, feature: Mapping[str, Any]) -> Alert:
        """Make a record from one GeoJSON feature that this package downloaded.

        Args:
            feature: A feature with ``properties`` and ``geometry``, such as one
                item of ``get_all()["features"]``.

        Returns:
            The typed record.

        Raises:
            ValueError: If a column is missing or a value cannot be read.

        Examples:
            >>> Alert.from_feature(_EXAMPLE).office
            'KSTO'
        """
        properties = feature.get("properties") or {}
        try:
            cap_id = properties["CAP_ID"]
            message_type = properties["MSG_TYPE"]
            product_type = properties["PROD_TYPE"]
            url = properties["URL"]
        except KeyError as error:
            raise ValueError(f"NWS's alert has no {error.args[0]} column") from error
        event = _optional_text(properties.get("EVENT"))
        try:
            event_number = None if event is None else int(event)
        except ValueError as error:
            raise ValueError(f"NWS's EVENT value {event!r} is not a number") from error
        return cls(
            cap_id=cap_id,
            message_type=message_type,
            product_type=product_type,
            vtec=_optional_text(properties.get("VTEC")),
            phenomenon=_optional_text(properties.get("PHENOM")),
            significance=_optional_text(properties.get("SIG")),
            office=_optional_text(properties.get("WFO")),
            event_number=event_number,
            issued_at=_parse_time(properties.get("ISSUANCE"), "ISSUANCE"),
            expires_at=_parse_time(properties.get("EXPIRATION"), "EXPIRATION"),
            onset_at=_optional_time(properties.get("ONSET"), "ONSET"),
            ends_at=_optional_time(properties.get("ENDS"), "ENDS"),
            url=url,
            geometry=dict(feature.get("geometry") or {}),
        )


_EXAMPLE = {
    "geometry": {"type": "Polygon", "coordinates": []},
    "properties": {
        "CAP_ID": "urn:oid:2",
        "MSG_TYPE": "FLS",
        "PROD_TYPE": "Flood Advisory",
        "VTEC": "/O.NEW.KSTO.FA.Y.0014.261118T1543Z-261118T1945Z/",
        "PHENOM": "FA",
        "SIG": "Y",
        "WFO": "KSTO",
        "EVENT": "0014",
        "ISSUANCE": "2026-11-18T07:43:00-08:00",
        "EXPIRATION": "2026-11-18T11:45:00-08:00",
        "ONSET": "2026-11-18T07:43:00-08:00",
        "ENDS": "2026-11-18T11:45:00-08:00",
        "URL": "https://api.weather.gov/alerts/urn:oid:2",
    },
}
