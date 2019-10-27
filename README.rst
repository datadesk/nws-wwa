nws-wwa
=======

Download watch, warning and advisory data from the National Weather Service

.. image:: https://travis-ci.org/datadesk/nws-wwa.svg?branch=master
    :target: https://travis-ci.org/datadesk/nws-wwa

Installation
------------

::

    $ pipenv install nws-wwa


Command-line usage
------------------

::

    Usage: nwswwa [OPTIONS] COMMAND [ARGS]...

    A command-line interface for downloading watch, warning and advisory data
    from the National Weather Service. Returns GeoJSON.

    Options:
    --help  Show this message and exit.

    Commands:
    all       All watch, warning and advisory data
    hazards   All hazard data
    warnings  All warnings data


Download data from the National Weather Service. ::

    $ nwswwa all
    $ nwswwa hazards
    $ nwswwa warnings


Python usage
------------

Import the library. ::

    >>> import nws_wwa
    >>> data = nws_wwa.all()
    >>> data = nws_wwa.hazards()
    >>> data = nws_wwa.warnings()


Contributing
------------

Install dependencies for development. ::

    $ pipenv install --dev

Run tests.::

    $ make test

Shipping new version to PyPI. ::

    $ make ship


Developing the CLI
------------------

The command-line interface is implemented using Click and setuptools. To install it locally for development inside your virtual environment, run the following installation command, as `prescribed by the Click documentation <https://click.palletsprojects.com/en/7.x/setuptools/#setuptools-integration>`_. ::

    $ pip install --editable .
