Download watch, warning and advisory data from the National Weather Service

Hourly scrapes powered by a GitHub Action are stored in the `data` directory.

## Installation

```bash
pipenv install nws-wwa
```

## Command-line usage

```bash
Usage: nwswwa [OPTIONS] COMMAND [ARGS]...

A command-line interface for downloading watch, warning and advisory data
from the National Weather Service. Returns GeoJSON.

Options:
--help  Show this message and exit.

Commands:
all       All watch, warning and advisory data
hazards   All hazard data
warnings  All warnings data
```

Download data from the National Weather Service.

```bash
nwswwa all
nwswwa hazards
nwswwa warnings
```

## Python usage

Import the library.

```python
>>> import nws_wwa
>>> data = nws_wwa.get_all()
>>> data = nws_wwa.get_hazards()
>>> data = nws_wwa.get_warnings()
```

## Contributing

Install dependencies for development.

```bash
pipenv install --dev
```

Run tests.

```bash
make test
```

Shipping new version to PyPI.

```bash
make ship
```

## Developing the CLI

The command-line interface is implemented using Click and setuptools. To install it locally for development inside your virtual environment, run the following installation command, as prescribed by the [Click documentation](https://click.palletsprojects.com/en/7.x/setuptools/#setuptools-integration).

```bash
pip install --editable .
```
