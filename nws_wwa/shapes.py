"""Read the shapefile NWS publishes, with pyogrio and shapely."""

from __future__ import annotations

from typing import Any

import shapely
from geojson import Feature, FeatureCollection, MultiPolygon, Polygon
from pyogrio.raw import read


def _lists(value: Any) -> Any:
    """Turn the tuples shapely returns into the lists GeoJSON uses.

    Args:
        value: A coordinate, or any nesting of coordinates in tuples.

    Returns:
        The same numbers in the same order, with every tuple made a list.

    Examples:
        >>> _lists((((0.0, 1.0), (2.0, 3.0)),))
        [[[0.0, 1.0], [2.0, 3.0]]]
    """
    if isinstance(value, tuple | list):
        return [_lists(item) for item in value]
    return value


def to_geometry(shape: shapely.Geometry) -> Polygon | MultiPolygon:
    """Turn a shapely polygon or multipolygon into a GeoJSON one.

    Args:
        shape: The shapely geometry.

    Returns:
        A GeoJSON ``Polygon`` or ``MultiPolygon`` with the same coordinates in
        the same order.

    Raises:
        ValueError: If the shape is not a polygon or multipolygon.

    Examples:
        >>> square = shapely.from_wkt("POLYGON ((0 0, 1 0, 1 1, 0 0))")
        >>> to_geometry(square)["coordinates"]
        [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 0.0]]]
    """
    kind = shape.geom_type
    coordinates = _lists(shape.__geo_interface__["coordinates"])
    if kind == "Polygon":
        return Polygon(coordinates)
    if kind == "MultiPolygon":
        return MultiPolygon(coordinates)
    raise ValueError(f"unsupported geometry type {kind}")


def read_shapefile_zip(content: bytes) -> FeatureCollection:
    """Read a zipped shapefile into GeoJSON.

    Args:
        content: The bytes of a zip file that holds a shapefile.

    Returns:
        A GeoJSON feature collection.

    Raises:
        RuntimeError: If GDAL cannot read the file.
        ValueError: If a shape is not a polygon or multipolygon.

    Examples:
        >>> data = read_shapefile_zip(zip_bytes)  # doctest: +SKIP
    """
    meta, _, geometries, columns = read(content, encoding="utf-8")
    shapes = shapely.from_wkb(geometries)
    features = []
    for i, shape in enumerate(shapes):
        properties: dict[str, Any] = {}
        for name, column in zip(meta["fields"], columns, strict=True):
            value = column[i]
            properties[str(name)] = value.item() if hasattr(value, "item") else value
        features.append(Feature(geometry=to_geometry(shape), properties=properties))
    return FeatureCollection(features)
