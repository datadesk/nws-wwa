```{include} _templates/nav.html
```

# nws-wwa

Download watch, warning and advisory data from the National Weather Service

```{contents} Table of contents
:local:
:depth: 2
```

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
import nws_wwa

data = nws_wwa.get_all()
data = nws_wwa.get_hazards()
data = nws_wwa.get_warnings()
```

## Contributing

Install dependencies for development.

```bash
pipenv install --dev
```

Run tests.

```bash
pipenv run python setup.py test
```

## Developing the CLI

The command-line interface is implemented using Click and setuptools. To install it locally for development inside your virtual environment, run the following installation command, as prescribed by the [Click documentation](https://click.palletsprojects.com/en/7.x/setuptools/#setuptools-integration).

```bash
pipenv run pip install --editable .
```

## Links

* Docs: [palewi.re/docs/nws-wwa/](https://palewi.re/docs/nws-wwa/)
* Issues: [github.com/datadesk/nws-wwa/issues](https://github.com/datadesk/nws-wwa/issues)
* Packaging: [pypi.python.org/pypi/nws-wwa](https://pypi.python.org/pypi/nws-wwa)
* Testing: [github.com/datadesk/nws-wwa/actions](https://github.com/datadesk/nws-wwa/actions)
