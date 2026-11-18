"""Methods for downloading watch, warning and advisory data from the National Weather Service."""

from __future__ import annotations

import io
import tarfile
import zipfile

import fiona
import fiona.errors
from geojson import Feature, FeatureCollection

from .errors import NWSDataError, NWSError
from .fetch import DEFAULT_TIMEOUT, download_file
from .options import FEED_LIST, Feed
from .records import Alert

__all__ = [
    "FEED_LIST",
    "Alert",
    "Feed",
    "NWSDataError",
    "NWSError",
    "get_alert_records",
    "get_all",
    "get_hazards",
    "get_warnings",
]


def get_all(
    verbose: bool = False, timeout: float = DEFAULT_TIMEOUT
) -> FeatureCollection:
    """Get all watch, warning and advisory data.

    Args:
        verbose: Print each request to standard error. Defaults to False.
        timeout: Seconds to wait for NWS on each try. Defaults to 60.

    Returns:
        A GeoJSON feature collection with one feature for each alert shape.

    Raises:
        NWSError: If NWS cannot be reached after several tries, or answers
            with an error.
        NWSDataError: If the file arrives but cannot be read.

    Examples:
        >>> import nws_wwa
        >>> data = nws_wwa.get_all()
    """
    return _parse_shapefile(Feed.ALL.file_name, verbose, timeout)


def get_hazards(
    verbose: bool = False, timeout: float = DEFAULT_TIMEOUT
) -> FeatureCollection:
    """Get all hazards data.

    Args:
        verbose: Print each request to standard error. Defaults to False.
        timeout: Seconds to wait for NWS on each try. Defaults to 60.

    Returns:
        A GeoJSON feature collection with one feature for each alert shape.

    Raises:
        NWSError: If NWS cannot be reached after several tries, or answers
            with an error.
        NWSDataError: If the file arrives but cannot be read.

    Examples:
        >>> import nws_wwa
        >>> data = nws_wwa.get_hazards()
    """
    return _parse_shapefile(Feed.HAZARDS.file_name, verbose, timeout)


def get_warnings(
    verbose: bool = False, timeout: float = DEFAULT_TIMEOUT
) -> FeatureCollection:
    """Get all warning data.

    Args:
        verbose: Print each request to standard error. Defaults to False.
        timeout: Seconds to wait for NWS on each try. Defaults to 60.

    Returns:
        A GeoJSON feature collection with one feature for each alert shape.

    Raises:
        NWSError: If NWS cannot be reached after several tries, or answers
            with an error.
        NWSDataError: If the file arrives but cannot be read.

    Examples:
        >>> import nws_wwa
        >>> data = nws_wwa.get_warnings()
    """
    return _parse_shapefile(Feed.WARNINGS.file_name, verbose, timeout)


def get_alert_records(
    feed: Feed | str = "all",
    verbose: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
) -> list[Alert]:
    """Download one of the three feeds as typed records instead of GeoJSON.

    Each record has numbers already parsed and timezone-aware UTC times. See
    ``Alert`` for every field.

    Args:
        feed: Which file to download, as a ``Feed`` or its short name: "all",
            "hazards" or "warnings". Defaults to "all".
        verbose: Print each request to standard error. Defaults to False.
        timeout: Seconds to wait for NWS on each try. Defaults to 60.

    Returns:
        A list of ``Alert`` records, one for each shape in the file.

    Raises:
        NWSError: If NWS cannot be reached after several tries, or answers
            with an error.
        NWSDataError: If a row from NWS is missing a column or has a value
            that cannot be read. This is also a ``ValueError``.
        ValueError: If the feed name is not one of the three.

    Examples:
        >>> import nws_wwa
        >>> records = nws_wwa.get_alert_records("hazards")
        >>> for alert in records:
        ...     print(alert.product_type, alert.office, alert.expires_at)
    """
    data = _parse_shapefile(Feed(feed).file_name, verbose, timeout)
    try:
        return [Alert.from_feature(feature) for feature in data["features"]]
    except ValueError as error:
        raise NWSDataError(str(error)) from error


def _parse_shapefile(
    name: str, verbose: bool = False, timeout: float = DEFAULT_TIMEOUT
) -> FeatureCollection:
    """Download one of NWS's shapefile archives and convert it to GeoJSON.

    Args:
        name: The file name on the NWS server, such as "current_all.tar.gz".
        verbose: Print each request to standard error. Defaults to False.
        timeout: Seconds to wait for NWS on each try. Defaults to 60.

    Returns:
        A GeoJSON feature collection.

    Raises:
        NWSError: If NWS cannot be reached or answers with an error.
        NWSDataError: If the file is not a readable shapefile archive.

    Examples:
        >>> data = _parse_shapefile("current_warnings.tar.gz")
    """
    content = download_file(name, verbose=verbose, timeout=timeout)
    buffer = io.BytesIO(bytes(content))

    try:
        # Untar it
        file_dict = _untar(buffer)
        if not any(n.endswith(".shp") for n in file_dict):
            raise NWSDataError(f"The file {name} has no shapefile inside")

        # Stuff it into a zip
        zf = _zip(file_dict)

        # Ask fiona to read to the zip, and convert the shapes to GeoJSON features
        with fiona.BytesCollection(zf.getvalue()) as shp:
            feature_list = [
                Feature(geometry=obj["geometry"], properties=dict(obj["properties"]))
                for obj in shp
            ]
    except (tarfile.TarError, EOFError, OSError, fiona.errors.FionaError) as error:
        raise NWSDataError(f"The file {name} could not be read: {error}") from error

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
