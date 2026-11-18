# nws-wwa

Download the current watches, warnings and advisories from the [National Weather Service](https://www.weather.gov/) (NWS) as GeoJSON or typed Python records.

**This is a copy of NWS data, not an official alert.** The files can be minutes old, and a download can fail. For anything that affects safety, use NWS itself: [weather.gov](https://www.weather.gov/), NOAA Weather Radio or Wireless Emergency Alerts.

## Install

```sh
uv add nws-wwa
```

## Use it from the command line

```sh
nwswwa all > all.json
nwswwa hazards --timeout 120
nwswwa warnings --verbose > warnings.json
```

The commands are `all`, `hazards` and `warnings`. Each prints GeoJSON. `--verbose` prints each request to standard error, so it never mixes into the JSON.

## Use it from Python

```python
import nws_wwa

data = nws_wwa.get_all()  # GeoJSON
records = nws_wwa.get_alert_records("hazards")  # typed records
print(records[0].product_type, records[0].office, records[0].expires_at)
```

`get_all`, `get_hazards` and `get_warnings` work as they always have. `get_alert_records` is new. It gives you `Alert` records with numbers already parsed and times in UTC.

## Use your own request function

Some projects send every web request through their own helper, for shared retries, logging or proxy settings. Pass that helper as `get` and the package will use it instead of `requests.get`. It is called like `get(url, timeout=seconds)` and must return something with a `status_code` and the file's `content` as bytes. The timeout and the retries still work, and failures still raise `NWSError`.

```python
import requests

import nws_wwa
from nws_wwa import Reply


def my_get(url: str, *, timeout: float) -> Reply:
    print("Asking for", url)
    return requests.get(url, timeout=timeout, headers={"User-Agent": "my-project"})


data = nws_wwa.get_all(get=my_get)
```

The `Fetcher` and `Reply` types describe this, so a type checker can confirm your function fits. If your function raises one of the `requests` library's errors, such as a timeout, the package tries again just as it does for its own requests. Any other error is passed on to you.

## Working on the code

This repository's full history is about 12.9 GB on GitHub, because the scraped data files were saved to it for years. Copy only the latest version:

```bash
git clone --depth 1 https://github.com/datadesk/nws-wwa.git
```

The automated checks do the same, so the version number comes from a tag only on a tagged release.

## Things to know

* **It is a copy, and it can be old.** NWS rewrites the files every few minutes, but this package only downloads when you ask it to.
* **Python 3.11 to 3.14 work.** The shapefiles are read with pyogrio, which needs numpy, so the install is about 100 MB.
* **Downloads retry.** A request waits 60 seconds, then tries again on network errors and server errors, and raises `nws_wwa.NWSError` if it still fails.
* **The same alert can fill several rows.** Count alerts by `CAP_ID` or `VTEC`, not by rows.
* **The data comes from NWS.** NWS says its web pages are in the public domain and provided "as is". The documentation quotes its disclaimer. The code is MIT.
* **AI helped write this package.** AI tools assisted in writing its code, tests and documentation. A person directed and reviewed the work.

The documentation has the full field reference and what each kind of product means.

### Links

* Docs: [palewi.re/docs/nws-wwa/](https://palewi.re/docs/nws-wwa/)
* Source data: [tgftp.nws.noaa.gov/SL.us008001/DF.sha/DC.cap/DS.WWA/](https://tgftp.nws.noaa.gov/SL.us008001/DF.sha/DC.cap/DS.WWA/)
* Issues: [github.com/datadesk/nws-wwa/issues](https://github.com/datadesk/nws-wwa/issues)
* Packaging: [pypi.python.org/pypi/nws-wwa](https://pypi.python.org/pypi/nws-wwa)
* Testing: [github.com/datadesk/nws-wwa/actions](https://github.com/datadesk/nws-wwa/actions)
