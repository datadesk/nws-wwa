"""Read the shapefile NWS publishes, with pyogrio and without shapely."""

from __future__ import annotations

import struct
from typing import Any

from geojson import Feature, FeatureCollection, MultiPolygon, Polygon
from pyogrio.raw import read


def _polygon(buf: bytes, pos: int) -> tuple[list[list[list[float]]], int]:
    """Read one polygon from well-known binary (WKB).

    Args:
        buf: The bytes of the geometry.
        pos: Where the polygon starts.

    Returns:
        The rings of the polygon, and the position just after it.

    Raises:
        ValueError: If it is not a 2D polygon.

    Examples:
        >>> wkb = bytes.fromhex("01030000000100000004000000" + "00" * 64)
        >>> len(_polygon(wkb, 0)[0][0])
        4
    """
    order = "<" if buf[pos] == 1 else ">"
    (kind,) = struct.unpack_from(order + "I", buf, pos + 1)
    if kind != 3:
        raise ValueError(f"unsupported geometry type {kind}")
    (count,) = struct.unpack_from(order + "I", buf, pos + 5)
    pos += 9
    rings = []
    for _ in range(count):
        (n,) = struct.unpack_from(order + "I", buf, pos)
        pts = struct.unpack_from(f"{order}{2 * n}d", buf, pos + 4)
        rings.append([[pts[i], pts[i + 1]] for i in range(0, 2 * n, 2)])
        pos += 4 + 16 * n
    return rings, pos


def wkb_to_geometry(wkb: bytes) -> Polygon | MultiPolygon:
    """Turn well-known binary into a GeoJSON polygon or multipolygon.

    Args:
        wkb: The geometry as WKB bytes.

    Returns:
        A GeoJSON ``Polygon`` or ``MultiPolygon``.

    Raises:
        ValueError: If the geometry is not a 2D polygon or multipolygon.
    """
    buf = bytes(wkb)
    order = "<" if buf[0] == 1 else ">"
    (kind,) = struct.unpack_from(order + "I", buf, 1)
    if kind == 3:
        return Polygon(_polygon(buf, 0)[0])
    if kind == 6:
        (count,) = struct.unpack_from(order + "I", buf, 5)
        pos, polygons = 9, []
        for _ in range(count):
            rings, pos = _polygon(buf, pos)
            polygons.append(rings)
        return MultiPolygon(polygons)
    raise ValueError(f"unsupported geometry type {kind}")


def read_shapefile_zip(content: bytes) -> FeatureCollection:
    """Read a zipped shapefile into GeoJSON.

    Args:
        content: The bytes of a zip file that holds a shapefile.

    Returns:
        A GeoJSON feature collection.

    Raises:
        RuntimeError: If GDAL cannot read the file.
        ValueError: If a shape is not a 2D polygon.
    """
    meta, _, geometries, columns = read(content, encoding="utf-8")
    features = []
    for i, wkb in enumerate(geometries):
        properties: dict[str, Any] = {}
        for name, column in zip(meta["fields"], columns, strict=True):
            value = column[i]
            properties[str(name)] = value.item() if hasattr(value, "item") else value
        features.append(Feature(geometry=wkb_to_geometry(wkb), properties=properties))
    return FeatureCollection(features)
