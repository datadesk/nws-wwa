#! /usr/bin/env python
# -*- coding: utf-8 -*-
import io
import fiona
import zipfile
import tarfile
import requests
from geojson import Feature, FeatureCollection


def get_all():
    """
    Get all watch, warning and advisory data.

    Returns a GeoJSON object.
    """
    return _parse_shapefile('current_all.tar.gz')


def get_hazards():
    """
    Get all hazards data.

    Returns a GeoJSON object.
    """
    return _parse_shapefile('current_hazards.tar.gz')


def get_warnings():
    """
    Get all warning data.

    Returns a GeoJSON object.
    """
    return _parse_shapefile('current_warnings.tar.gz')


def _parse_shapefile(name):
    """
    Downloads the provided shapefile from GeoMAC.

    Returns a GeoJSON object.
    """
    # Figure out the url
    domain = 'tgftp.nws.noaa.gov'
    base_dir = 'SL.us008001/DF.sha/DC.cap/DS.WWA'
    url = f'https://{domain}/{base_dir}/{name}'

    # Get the zipfile
    r = requests.get(url)
    buffer = io.BytesIO(bytes(r.content))
    file_dict = _untar(buffer)
    zf = _zip(file_dict)
    shp = fiona.BytesCollection(zf.getvalue())

    # Convert it GeoJSON and return it
    feature_list = [
        Feature(geometry=d['geometry'], properties=d['properties']) for d in shp
    ]
    return FeatureCollection(feature_list)


def _untar(fileobj):
    """
    Untar the provided file-like object.

    Returns a dict of the file-like objects inside the archive key to their names.
    """
    file_dict = {}
    with tarfile.open(fileobj=fileobj) as tar:
        for t in tar:
            if (t.isfile()):
                file_bytes = tar.extractfile(t).read()
                file_buffer = io.BytesIO(file_bytes)
                file_dict[t.name] = file_buffer
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
        # Download each piece of the shapefile ...
        for n, f in file_dict.items():
            # ... and add it to the in-memory zipfile
            zf.writestr(n, f.getvalue())

    return buffer
