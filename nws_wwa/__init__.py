"""Methods for downloading watch, warning and advisory data from the National Weather Service."""

from __future__ import annotations

import io
import tarfile
import zipfile

import fiona
import requests
from geojson import Feature, FeatureCollection

from .options import FEED_LIST, Feed
from .records import Alert

__all__ = [
    "FEED_LIST",
    "Alert",
    "Feed",
    "get_alert_records",
    "get_all",
    "get_hazards",
    "get_warnings",
]


def get_all():
    """
    Get all watch, warning and advisory data.

    Returns a GeoJSON object.
    """
    return _parse_shapefile("current_all.tar.gz")


def get_hazards():
    """
    Get all hazards data.

    Returns a GeoJSON object.
    """
    return _parse_shapefile("current_hazards.tar.gz")


def get_warnings():
    """
    Get all warning data.

    Returns a GeoJSON object.
    """
    return _parse_shapefile("current_warnings.tar.gz")


def get_alert_records(feed: Feed | str = "all") -> list[Alert]:
    """Download one of the three feeds as typed records instead of GeoJSON.

    Each record has numbers already parsed and timezone-aware UTC times. See
    ``Alert`` for every field.

    Args:
        feed: Which file to download, as a ``Feed`` or its short name: "all",
            "hazards" or "warnings". Defaults to "all".

    Returns:
        A list of ``Alert`` records, one for each shape in the file.

    Raises:
        ValueError: If a row from NWS is missing a column or has a value that
            cannot be read, or if the feed name is not one of the three.

    Examples:
        >>> import nws_wwa
        >>> records = nws_wwa.get_alert_records("hazards")
        >>> for alert in records:
        ...     print(alert.product_type, alert.office, alert.expires_at)
    """
    data = _parse_shapefile(Feed(feed).file_name)
    return [Alert.from_feature(feature) for feature in data["features"]]


def _parse_shapefile(name):
    """
    Downloads the provided shapefile from GeoMAC.

    Returns a GeoJSON object.
    """
    # Figure out the url
    domain = "tgftp.nws.noaa.gov"
    base_dir = "SL.us008001/DF.sha/DC.cap/DS.WWA"
    url = f"https://{domain}/{base_dir}/{name}"

    # Get the zipfile
    r = requests.get(url)
    buffer = io.BytesIO(bytes(r.content))

    # Untar it
    file_dict = _untar(buffer)

    # Stuff it into a zip
    zf = _zip(file_dict)

    # Ask fiona to read to the zip
    shp = fiona.BytesCollection(zf.getvalue())

    # Convert the shp to GeoJSON features
    feature_list = [
        Feature(geometry=obj["geometry"], properties=dict(obj["properties"]))
        for obj in shp
    ]

    # We're done here
    return FeatureCollection(feature_list)


def _untar(fileobj):
    """
    Untar the provided file-like object.

    Returns a dict of the file-like objects inside the archive key to their names.
    """
    file_dict = {}
    # Open the tarfile
    with tarfile.open(fileobj=fileobj) as tar:
        # Walk thru each member
        for t in tar:
            # if it's a file ...
            if t.isfile():
                # ... extract it ...
                member = tar.extractfile(t)
                assert member is not None
                file_bytes = member.read()
                # .. read it into a file-like object ...
                file_buffer = io.BytesIO(file_bytes)
                # ... add it to our file dict with its name.
                file_dict[t.name] = file_buffer
    # Pass it all back
    return file_dict


def _zip(file_dict):
    """
    Zips up the provided dict of file-like objects.

    Returns a single file-like object with all the file archived together.
    """
    # Create in-memory file
    buffer = io.BytesIO()

    # Turn it into a zipfile
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Walk thru each piece in the tarfile ...
        for n, f in file_dict.items():
            # ... and add it to the in-memory zipfile
            zf.writestr(n, f.getvalue())
    # Pass back the buffer with the zip in it
    return buffer
