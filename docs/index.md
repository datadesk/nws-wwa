# nws-wwa

Download watch, warning and advisory data from the [National Weather Service](https://www.spc.noaa.gov/products/wwa/)

```{contents} Table of contents
:local:
:depth: 2
```

## Installation

```bash
uv add nws-wwa
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
uv sync --all-groups
```

Run tests.

```bash
make test
```

## Developing the CLI

The command-line interface is implemented using Click and setuptools. `uv sync --all-groups` installs it into the project's virtual environment, so you can run it with `uv run nwswwa`.

## Other resources

* Source: [www.spc.noaa.gov/products/wwa/](https://www.spc.noaa.gov/products/wwa/)
* Issues: [github.com/datadesk/nws-wwa/issues](https://github.com/datadesk/nws-wwa/issues)
* Packaging: [pypi.python.org/pypi/nws-wwa](https://pypi.python.org/pypi/nws-wwa)
* Testing: [github.com/datadesk/nws-wwa/actions](https://github.com/datadesk/nws-wwa/actions)
