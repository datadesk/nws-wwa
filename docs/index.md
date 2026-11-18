# nws-wwa

Download the current watches, warnings and advisories from the [National Weather Service](https://www.weather.gov/) (NWS)

```{contents} Table of contents
:local:
:depth: 2
```

## Read this first

**This is a copy of NWS data. It is not an official alert.**

* NWS rewrites the three files every few minutes. When I watched on 2026-11-18, one file changed about two minutes after the one before it. NWS does not promise a schedule that I could find. This package downloads only when you ask, so what you get is as old as the moment of your download.
* A download can fail or return an old file. NWS says on its [disclaimer page](https://www.weather.gov/disclaimer): "Timely delivery of data and products from this server through the Internet is not guaranteed."
* For anything that affects safety, use the official NWS channels. NWS lists them as NOAA Weather Radio, NOAA Weather Wire, EMWIN and NOAAPORT, and you can read alerts on [weather.gov](https://www.weather.gov/).
* Do not present this data as official government material. NWS asks users not to "modify its content and then present it as official government material", and not to use its name in a way that "implies an endorsement or affiliation with NOAA/NWS".

## Installation

```bash
uv add nws-wwa
```

The package reads NWS's shapefiles with [Fiona](https://fiona.readthedocs.io/). Fiona ships ready-made files for Python 3.11, 3.12 and 3.13 on Linux, macOS and Windows. For Python 3.14 you would have to build it yourself.

## Quick start

From the shell, print GeoJSON for every current alert shape.

```bash
nwswwa all > all.json
```

From Python, ask for typed records and read their fields.

```python
import nws_wwa

for alert in nws_wwa.get_alert_records("hazards"):
    print(alert.product_type, alert.office, alert.significance_name, alert.expires_at)
```

## What is in the three files

NWS publishes three files, and each one holds the shapes (polygons) of the areas where alerts are in effect. The package calls them feeds.

| Feed | Command | Python function | What it holds |
| --- | --- | --- | --- |
| `all` | `nwswwa all` | `get_all()` | Every shape in NWS's `current_all` file, including statements that have no VTEC code |
| `hazards` | `nwswwa hazards` | `get_hazards()` | The same, without the products that have no VTEC code. In the copy I checked, it was exactly the `all` file minus its 30 statements |
| `warnings` | `nwswwa warnings` | `get_warnings()` | A much smaller file. In the copies I checked it held only a few short-lived warnings, such as a Special Marine Warning or a Flash Flood Warning. I could not find NWS's own description of why |

On 2026-11-18, `all` had 1,061 rows, `hazards` had 1,031 and `warnings` had 1. Your counts will differ.

## What a watch, a warning and an advisory mean

In general:

* A **watch** means conditions are right for the hazard to develop. It is time to get ready.
* A **warning** means the hazard is happening or about to happen. It is time to act.
* An **advisory** is for less serious conditions that can still cause real trouble.
* A **statement** gives more detail or an update.

These are everyday summaries, not NWS's wording, and the exact rules differ for each kind of hazard and each forecast office. Read NWS's own definition for the product you care about.

## Fields

Each GeoJSON feature has these properties, named as NWS names them. The typed `Alert` record has the same information with nicer names, parsed numbers and UTC times.

| NWS property | `Alert` field | Type | What it is |
| --- | --- | --- | --- |
| `CAP_ID` | `cap_id` | text | NWS's unique identifier for the alert, in the Common Alerting Protocol (CAP) format |
| `MSG_TYPE` | `message_type` | text | The three-letter code of the text bulletin, such as `FFW` or `SMW` |
| `PROD_TYPE` | `product_type` | text | The name of the product, such as "Flash Flood Warning" |
| `VTEC` | `vtec` | text or none | The Valid Time Event Code NWS uses to follow an event from first message to end. None for statements |
| `PHENOM` | `phenomenon` | text or none | Two-letter code for the kind of weather, such as `FF` for flash flood or `MA` for a marine hazard |
| `SIG` | `significance` | text or none | One letter for how serious it is. See the table below |
| `WFO` | `office` | text or none | Four-letter code of the forecast office, such as `KMFL` |
| `EVENT` | `event_number` | whole number or none | The office's running number for the event. NWS writes it as four digits, such as `0365` |
| `ISSUANCE` | `issued_at` | UTC time | When NWS issued the message |
| `EXPIRATION` | `expires_at` | UTC time | When the message expires |
| `ONSET` | `onset_at` | UTC time or none | When the hazard is expected to begin |
| `ENDS` | `ends_at` | UTC time or none | When the hazard is expected to end. Empty for about 3 percent of the rows I checked |
| `URL` | `url` | text | The address of the alert in the NWS API |
| the shape | `geometry` | dictionary | A GeoJSON polygon or multipolygon, in longitude and latitude |

NWS writes each time in the local time of the area, with the offset at the end, such as `2026-11-18T07:43:00-08:00`. The GeoJSON keeps that text exactly. The typed records convert it to UTC.

The one-letter `SIG` codes, from NWS's [VTEC instruction (NWSI 10-1703, April 6, 2021)](https://www.weather.gov/media/directives/010_pdfs/pd01017003curr.pdf):

| Code | Meaning |
| --- | --- |
| `W` | Warning |
| `A` | Watch |
| `Y` | Advisory |
| `S` | Statement |
| `F` | Forecast |
| `O` | Outlook |
| `N` | Synopsis |

An `Alert` has a `significance_name` property that gives this word.

**The same alert can fill several rows.** On 2026-11-18, the 1,061 rows of the `all` file held 537 different `CAP_ID` values. Count alerts by `CAP_ID` or `VTEC`, not by rows. I did not find out why NWS repeats them.

The shapes use longitude and latitude (EPSG:4326).

## Command-line usage

```bash
Usage: nwswwa [OPTIONS] COMMAND [ARGS]...

  A command-line interface for downloading watch, warning and advisory data
  from the National Weather Service.

  Returns GeoJSON.

Options:
  --help  Show this message and exit.

Commands:
  all       All watch, warning and advisory data
  hazards   All hazard data
  warnings  All warnings data
```

Every command takes two options.

* `--timeout` is how many seconds to wait for NWS on each try. The default is 60.
* `--verbose` prints each request to standard error. It never mixes into the JSON on standard output.

```bash
nwswwa all > all.json
nwswwa hazards --timeout 120
nwswwa warnings --verbose > warnings.json
```

If NWS cannot be reached after four tries, the command prints one line that starts with `Error:` and exits with code 1.

## Python usage

```python
import nws_wwa

data = nws_wwa.get_all()
data = nws_wwa.get_hazards()
data = nws_wwa.get_warnings(timeout=120, verbose=True)

records = nws_wwa.get_alert_records("all")
```

`get_alert_records` takes a feed name (`"all"`, `"hazards"` or `"warnings"`) or a `nws_wwa.Feed` value.

## Reliable downloads

Each request waits 60 seconds. If NWS cannot be reached, takes too long, or answers with a server error or "too many requests", the package waits and tries again, up to four tries in all, with a longer pause each time. A "not found" fails right away. When it gives up it raises `nws_wwa.NWSError`, which has the web address and, if there was one, the status code. If the file arrives but cannot be read, it raises `nws_wwa.NWSDataError`, which is also a `ValueError`.

NWS asks automated users to be gentle. Its [disclaimer page](https://www.weather.gov/disclaimer) says "If a Web Service isn't available users should limit the number of retries to 1 minute intervals" and that "If you are querying a service for short fused warnings it may make sense to query our service once or twice a minute". This package's own retries pause for seconds, not minutes, so do not run it in a tight loop.

## Use your own request function

Some projects send every web request through their own helper. Pass it as `get`.

```python
import requests

import nws_wwa
from nws_wwa import Reply


def my_get(url: str, *, timeout: float) -> Reply:
    return requests.get(url, timeout=timeout, headers={"User-Agent": "my-project"})


data = nws_wwa.get_all(get=my_get)
```

It is called like `get(url, timeout=seconds)` and must return something with `status_code` and `content`. The `Fetcher` and `Reply` types describe this.

## Where the data comes from and how to credit it

The package downloads three files from `https://tgftp.nws.noaa.gov/SL.us008001/DF.sha/DC.cap/DS.WWA/`: `current_all.tar.gz`, `current_hazards.tar.gz` and `current_warnings.tar.gz`. Each one is an archive of a shapefile.

NWS says that "The information on National Weather Service (NWS) Web pages are in the public domain, unless specifically noted otherwise, and may be used without charge for any lawful purpose so long as you do not: 1) claim it is your own (e.g., by claiming copyright for NWS information -- see below), 2) use it in a manner that implies an endorsement or affiliation with NOAA/NWS, or 3) modify its content and then present it as official government material." It also provides the information "as is," and says NWS "disclaims any and all warranties, whether express or implied". Read the full [NWS disclaimer](https://www.weather.gov/disclaimer). I did not find a separate page that applies these terms to the shapefile server specifically, so treat that as an assumption.

NWS does not ask for a credit line there, but crediting the National Weather Service is good practice. The package's code is MIT licensed.

This package only downloads the data. It is not made by NWS and is not endorsed by NWS.

## About this package

AI tools assisted in writing this package's code, tests and documentation. A person directed and reviewed the work.

## Contributing

This repository's full history is about 12.9 GB on GitHub, because the scraped data files were saved to it for years. Copy only the latest version.

```bash
git clone --depth 1 https://github.com/datadesk/nws-wwa.git
```

Install dependencies for development.

```bash
uv sync --all-groups
```

Run the checks. `make check` runs lint, the type check and the offline tests, which use small saved samples of real NWS files and never touch the internet.

```bash
make check
```

`make test` also measures how much of the code the tests run, counting each branch of an `if`. It fails if less than 95 percent is covered (it is 100 percent today). `make test-fast` runs the same tests without measuring. The automated checks measure coverage on the newest Python only.

The tests that call NWS itself are marked `live` and skipped by default. Run them with `make test-live`, or start the "Testing and deployment" workflow by hand on GitHub.

The command-line interface is built with Click. `uv sync --all-groups` installs it, so you can run it with `uv run nwswwa`.

## Other resources

* Source data: [tgftp.nws.noaa.gov/SL.us008001/DF.sha/DC.cap/DS.WWA/](https://tgftp.nws.noaa.gov/SL.us008001/DF.sha/DC.cap/DS.WWA/)
* Issues: [github.com/datadesk/nws-wwa/issues](https://github.com/datadesk/nws-wwa/issues)
* Packaging: [pypi.python.org/pypi/nws-wwa](https://pypi.python.org/pypi/nws-wwa)
* Testing: [github.com/datadesk/nws-wwa/actions](https://github.com/datadesk/nws-wwa/actions)
