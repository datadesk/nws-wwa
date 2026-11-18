"""Download NWS's alert files, with a timeout and retries."""

from __future__ import annotations

import random
import sys
import time
from typing import Protocol

import requests

from .errors import NWSError

DOMAIN = "tgftp.nws.noaa.gov"
"""The NWS server that publishes the files."""

BASE_PATH = "SL.us008001/DF.sha/DC.cap/DS.WWA"
"""The folder on the server that holds the three files."""

DEFAULT_TIMEOUT = 60.0
"""How many seconds to wait for NWS before giving up on one attempt."""

DEFAULT_TRIES = 4
"""How many times to try before raising an error."""

RETRY_STATUS_CODES = frozenset({408, 429})
"""Statuses worth another try. Every 5xx status is also worth another try."""


class Reply(Protocol):
    """What a request function must hand back: a status code and the file's bytes.

    A ``requests.Response`` fits this.
    """

    @property
    def status_code(self) -> int:
        """The web status, such as 200 or 404."""
        ...

    @property
    def content(self) -> bytes:
        """The body of the reply, as bytes."""
        ...


class Fetcher(Protocol):
    """A function that makes a web request for this package.

    Pass one as ``get`` to add retries, logging or custom headers. ``requests.get``
    fits this, and is the default.

    Examples:
        >>> import requests
        >>> fetcher: Fetcher = requests.get
    """

    def __call__(self, url: str, *, timeout: float) -> Reply:
        """Request a web address.

        Args:
            url: The address to request.
            timeout: The seconds to wait before giving up.

        Returns:
            The reply.
        """
        ...


def file_url(file_name: str) -> str:
    """Build the web address of one of NWS's files.

    Args:
        file_name: The name of the file, such as "current_all.tar.gz".

    Returns:
        The full address.

    Examples:
        >>> file_url("current_all.tar.gz")
        'https://tgftp.nws.noaa.gov/SL.us008001/DF.sha/DC.cap/DS.WWA/current_all.tar.gz'
    """
    return f"https://{DOMAIN}/{BASE_PATH}/{file_name}"


def download_file(
    file_name: str,
    verbose: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
    tries: int = DEFAULT_TRIES,
    get: Fetcher | None = None,
) -> bytes:
    """Download one of NWS's alert files and return its bytes.

    A download is tried again when NWS cannot be reached, takes too long, or
    answers with a server error or "too many requests". The wait before each
    new try doubles, starting at 2 seconds. Any other bad status, such as "not
    found", fails right away.

    Args:
        file_name: The name of the file, such as "current_all.tar.gz".
        verbose: Print each request to standard error. Defaults to False.
        timeout: Seconds to wait for NWS on each try. Defaults to 60.
        tries: How many tries to make in all. Defaults to 4.
        get: A function that makes the web request, such as ``requests.get``
            (the default). It is called as ``get(url, timeout=seconds)`` and
            must return something with ``status_code`` and ``content``. Its
            ``requests`` errors are retried like the default's. Any other error
            it raises is passed on untouched.

    Returns:
        The bytes of the file.

    Raises:
        NWSError: If every try fails, or NWS answers with a status that is not
            worth trying again.

    Examples:
        >>> data = download_file("current_warnings.tar.gz")
        >>> data = download_file("current_all.tar.gz", timeout=120, tries=2)
        >>> data = download_file("current_all.tar.gz", get=my_get)
    """
    fetch: Fetcher = get or requests.get
    url = file_url(file_name)
    problem = None
    for attempt in range(max(tries, 1)):
        if attempt:
            time.sleep(2**attempt + random.random())
        if verbose:
            print(f"Requesting {url}", file=sys.stderr)
        try:
            response = fetch(url, timeout=timeout)
        except (requests.ConnectionError, requests.Timeout) as error:
            problem = NWSError(f"Could not reach NWS at {url}: {error}", url=url)
            continue
        except requests.RequestException as error:
            raise NWSError(f"Request to {url} failed: {error}", url=url) from error

        status = response.status_code
        if status >= 500 or status in RETRY_STATUS_CODES:
            problem = NWSError(
                f"NWS sent back status {status} for {url}", url=url, status_code=status
            )
            continue
        if status >= 400:
            raise NWSError(
                f"NWS sent back status {status} for {url}", url=url, status_code=status
            )
        return response.content

    assert problem is not None
    raise problem
