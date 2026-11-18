"""Offline tests of the shapefile reader."""

import io
import struct
import tarfile

import pytest

from nws_wwa import NWSDataError, NWSError, _parse_shapefile, shapes

from .conftest import DATA, FakeResponse


def ring(points, order="<"):
    """Write one ring as WKB."""
    out = struct.pack(order + "I", len(points))
    for x, y in points:
        out += struct.pack(order + "dd", x, y)
    return out


def polygon(rings, order="<"):
    """Write a polygon as WKB, little or big endian."""
    flag = b"\x01" if order == "<" else b"\x00"
    out = flag + struct.pack(order + "II", 3, len(rings))
    return out + b"".join(ring(r, order) for r in rings)


SQUARE = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 0.0)]


@pytest.mark.parametrize("order", ["<", ">"])
def test_polygon_either_byte_order(order):
    """Little and big endian polygons read the same."""
    geometry = shapes.wkb_to_geometry(polygon([SQUARE], order))
    assert geometry["type"] == "Polygon"
    assert geometry["coordinates"] == [[list(p) for p in SQUARE]]


@pytest.mark.parametrize("order", ["<", ">"])
def test_multipolygon_either_byte_order(order):
    """Little and big endian multipolygons read the same."""
    flag = b"\x01" if order == "<" else b"\x00"
    wkb = flag + struct.pack(order + "II", 6, 2)
    wkb += polygon([SQUARE], order) + polygon([SQUARE, SQUARE], order)
    geometry = shapes.wkb_to_geometry(wkb)
    assert geometry["type"] == "MultiPolygon"
    assert [len(p) for p in geometry["coordinates"]] == [1, 2]


def test_other_shapes_are_refused():
    """A point is not a polygon, and it raises ValueError."""
    point = b"\x01" + struct.pack("<Idd", 1, 0.0, 0.0)
    with pytest.raises(ValueError, match="unsupported"):
        shapes.wkb_to_geometry(point)
    wkb = b"\x01" + struct.pack("<II", 6, 1) + point
    with pytest.raises(ValueError, match="unsupported"):
        shapes.wkb_to_geometry(wkb)


def test_saved_samples_read():
    """Every saved sample reads, and every shape has coordinates."""
    from nws_wwa import _untar, _zip

    for name in ["all", "hazards", "warnings"]:
        content = (DATA / f"sample_{name}.tar.gz").read_bytes()
        zipped = _zip(_untar(io.BytesIO(content))).getvalue()
        data = shapes.read_shapefile_zip(zipped)
        assert data["features"]
        for feature in data["features"]:
            assert feature["geometry"]["coordinates"]


def test_non_polygon_shapefile_is_a_data_error(monkeypatch, tmp_path):
    """A real shapefile of points raises NWSDataError, not a bare ValueError."""
    import numpy as np
    from pyogrio.raw import write

    from nws_wwa import fetch

    path = tmp_path / "points.shp"
    write(
        str(path),
        geometry=np.array([bytes(struct.pack("<BIdd", 1, 1, 1.0, 2.0))], dtype=object),
        field_data=[],
        fields=[],
        geometry_type="Point",
        crs="EPSG:4326",
    )
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for part in tmp_path.glob("points.*"):
            tar.add(part, arcname=part.name)
    monkeypatch.setattr(
        fetch.requests, "get", lambda *a, **k: FakeResponse(buffer.getvalue())
    )
    with pytest.raises(NWSDataError, match="could not be read"):
        _parse_shapefile("current_all.tar.gz")
    assert issubclass(NWSDataError, NWSError)
