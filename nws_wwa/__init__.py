import io
import tarfile
import zipfile

import fiona
import requests
from geojson import Feature, FeatureCollection


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
        Feature(geometry=d["geometry"], properties=d["properties"]) for d in shp
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
                file_bytes = tar.extractfile(t).read()
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
