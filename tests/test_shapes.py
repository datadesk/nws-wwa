"""Offline tests of the shapefile reader."""

import doctest
import io
import tarfile

import pytest
import shapely

from nws_wwa import NWSDataError, NWSError, _parse_shapefile, shapes

from .conftest import DATA, FakeResponse


def test_doctests():
    """The examples in the shapes module are correct."""
    assert doctest.testmod(shapes).failed == 0


def test_polygon_keeps_its_coordinates_and_winding():
    """Coordinates come back as lists, in the order given, whatever the winding."""
    clockwise = [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]
    geometry = shapes.to_geometry(shapely.Polygon(clockwise))
    assert geometry["type"] == "Polygon"
    assert geometry["coordinates"] == [[list(p) for p in clockwise]]
    assert isinstance(geometry["coordinates"][0][0], list)


def test_multipolygon_keeps_every_part():
    """A multipolygon keeps its parts and their holes."""
    square = [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 0.0)]
    hole = [(1.0, 1.0), (2.0, 1.0), (2.0, 2.0), (1.0, 1.0)]
    shape = shapely.MultiPolygon([(square, [hole]), (square, [])])
    geometry = shapes.to_geometry(shape)
    assert geometry["type"] == "MultiPolygon"
    assert [len(p) for p in geometry["coordinates"]] == [2, 1]


def test_other_shapes_are_refused():
    """A point is not a polygon, and it raises ValueError."""
    with pytest.raises(ValueError, match="unsupported geometry type Point"):
        shapes.to_geometry(shapely.Point(0, 0))


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
        geometry=np.array([shapely.to_wkb(shapely.Point(1.0, 2.0))], dtype=object),
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


def test_missing_shapefile_message_is_not_wrapped(monkeypatch):
    """The "no shapefile" error keeps its own message, with no "could not be read"."""
    from nws_wwa import fetch

    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        info = tarfile.TarInfo("readme.txt")
        info.size = 2
        tar.addfile(info, io.BytesIO(b"hi"))
    monkeypatch.setattr(
        fetch.requests, "get", lambda *a, **k: FakeResponse(buffer.getvalue())
    )
    with pytest.raises(NWSDataError) as caught:
        _parse_shapefile("current_all.tar.gz")
    assert str(caught.value) == "The file current_all.tar.gz has no shapefile inside"
