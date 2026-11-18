"""Offline tests of the optional ``get`` argument, with a fake request function."""

import pytest
import requests

import nws_wwa
from nws_wwa import Feed, Fetcher, NWSDataError, NWSError, Reply, fetch

from .conftest import FakeResponse


class Recorder:
    """A fake request function that plays back replies and remembers each call."""

    def __init__(self, *replies) -> None:
        self.replies = list(replies)
        self.urls: list[str] = []
        self.timeouts: list[float] = []

    def __call__(self, url: str, *, timeout: float) -> FakeResponse:
        self.urls.append(url)
        self.timeouts.append(timeout)
        reply = self.replies[min(len(self.urls), len(self.replies)) - 1]
        if isinstance(reply, Exception):
            raise reply
        return reply


class BareReply:
    """The least a reply needs: a status code and the bytes."""

    def __init__(self, content: bytes) -> None:
        self.status_code = 200
        self.content = content


@pytest.fixture
def good(sample):
    """A good reply."""
    return FakeResponse(sample("all"))


@pytest.fixture
def no_requests(monkeypatch):
    """Fail the test if the package falls back to ``requests.get``."""

    def refuse(*args, **kwargs):
        raise AssertionError("requests.get should not be called")

    monkeypatch.setattr(fetch.requests, "get", refuse)


def test_types_are_exported():
    """The two types are part of the public package."""
    assert nws_wwa.Fetcher is fetch.Fetcher
    assert nws_wwa.Reply is fetch.Reply
    assert {"Fetcher", "Reply"} <= set(nws_wwa.__all__)


def test_function_is_used_instead_of_requests(no_requests, good):
    """The caller's function makes the request, and requests is never used."""
    get = Recorder(good)
    data = nws_wwa.get_all(get=get)
    assert len(data["features"]) == 7
    assert get.urls == [fetch.file_url("current_all.tar.gz")]
    assert get.timeouts == [60.0]


@pytest.mark.parametrize(
    "call,name",
    [
        (nws_wwa.get_all, "all"),
        (nws_wwa.get_hazards, "hazards"),
        (nws_wwa.get_warnings, "warnings"),
        (nws_wwa.get_alert_records, "all"),
    ],
)
def test_every_download_function_accepts_get(no_requests, sample, call, name):
    """All four download functions take the argument."""
    get = Recorder(FakeResponse(sample(name)))
    assert call(get=get, timeout=9)
    assert get.timeouts == [9]


def test_records_accept_get(no_requests, sample):
    """The typed records use the function too, for any feed."""
    get = Recorder(FakeResponse(sample("hazards")))
    assert len(nws_wwa.get_alert_records(Feed.HAZARDS, get=get)) == 6
    assert get.urls[0].endswith("current_hazards.tar.gz")


def test_get_is_keyword_only(good):
    """``get`` cannot be given by position, so it never clashes with ``timeout``."""
    with pytest.raises(TypeError):
        nws_wwa.get_all(False, 60.0, Recorder(good))  # type: ignore[misc]


def test_reply_needs_only_status_and_content(no_requests, sample):
    """A reply with just ``status_code`` and ``content`` is enough."""
    get = Recorder(BareReply(sample("warnings")))
    assert len(nws_wwa.get_warnings(get=get)["features"]) == 1


def test_requests_errors_are_retried(no_requests, good):
    """The caller's function gets the same retries as the default."""
    get = Recorder(requests.ConnectionError("down"), requests.Timeout("slow"), good)
    assert nws_wwa.get_all(get=get)
    assert len(get.urls) == 3


def test_server_errors_are_retried(no_requests, good):
    """A 503 from the caller's function is tried again."""
    get = Recorder(FakeResponse(status_code=503), good)
    assert nws_wwa.get_all(get=get)
    assert len(get.urls) == 2


def test_gives_up_with_nws_error(no_requests):
    """After four failed tries the package raises NWSError."""
    get = Recorder(FakeResponse(status_code=500))
    with pytest.raises(NWSError):
        nws_wwa.get_all(get=get)
    assert len(get.urls) == 4


def test_not_found_is_not_retried(no_requests):
    """A 404 fails at once."""
    get = Recorder(FakeResponse(status_code=404))
    with pytest.raises(NWSError) as caught:
        nws_wwa.get_all(get=get)
    assert len(get.urls) == 1
    assert caught.value.status_code == 404


def test_other_errors_pass_through(no_requests):
    """An error that is not from requests reaches the caller untouched."""
    get = Recorder(KeyError("mine"))
    with pytest.raises(KeyError):
        nws_wwa.get_all(get=get)
    assert len(get.urls) == 1


def test_bad_file_is_a_data_error(no_requests):
    """A reply that is not a shapefile archive raises NWSDataError."""
    get = Recorder(FakeResponse(b"nope"))
    with pytest.raises(NWSDataError):
        nws_wwa.get_alert_records(get=get)


def test_default_still_uses_requests(fake_nws):
    """With no ``get``, the package asks through ``requests.get`` as before."""
    nws_wwa.get_all()
    assert len(fake_nws.urls) == 1


def test_requests_get_fits_the_type():
    """``requests.get`` can be assigned to the Fetcher type."""
    fetcher: Fetcher = requests.get
    assert callable(fetcher)
    assert Reply is fetch.Reply
