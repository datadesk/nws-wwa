"""Offline tests of the timeout, the retries and the error classes."""

import doctest

import pytest
import requests

import nws_wwa
from nws_wwa import NWSDataError, NWSError, errors, fetch

from .conftest import FakeResponse


class Recorder:
    """A fake ``requests.get`` that plays back replies and remembers each call."""

    def __init__(self, *replies) -> None:
        self.replies = list(replies)
        self.urls: list[str] = []
        self.timeouts: list[float] = []

    def __call__(self, url, *args, timeout=None, **kwargs):
        self.urls.append(url)
        self.timeouts.append(timeout)
        reply = self.replies[min(len(self.urls), len(self.replies)) - 1]
        if isinstance(reply, Exception):
            raise reply
        return reply


@pytest.fixture
def good(sample):
    """A good reply."""
    return FakeResponse(sample("warnings"))


def use(monkeypatch, recorder):
    """Make the package use a fake ``requests.get``."""
    monkeypatch.setattr(fetch.requests, "get", recorder)
    return recorder


def test_doctests():
    """The examples that run without the network are correct."""
    assert doctest.testmod(errors).failed == 0
    assert fetch.file_url("a.tar.gz").endswith("/DS.WWA/a.tar.gz")


def test_timeout_is_passed_along(monkeypatch, good):
    """The default timeout is 60 seconds and a caller can change it."""
    recorder = use(monkeypatch, Recorder(good))
    nws_wwa.get_warnings()
    nws_wwa.get_warnings(timeout=5)
    assert recorder.timeouts == [60.0, 5]


def test_retries_network_errors_then_succeeds(monkeypatch, good):
    """Connection errors and timeouts are tried again."""
    recorder = use(
        monkeypatch,
        Recorder(requests.ConnectionError("down"), requests.Timeout("slow"), good),
    )
    assert len(nws_wwa.get_warnings()["features"]) == 1
    assert len(recorder.urls) == 3


def test_retries_server_errors(monkeypatch, good):
    """A 503 or a 429 is tried again."""
    recorder = use(
        monkeypatch,
        Recorder(FakeResponse(status_code=503), FakeResponse(status_code=429), good),
    )
    nws_wwa.get_warnings()
    assert len(recorder.urls) == 3


def test_gives_up_after_four_tries(monkeypatch):
    """After four failures the last problem is raised as an NWSError."""
    recorder = use(monkeypatch, Recorder(FakeResponse(status_code=502)))
    with pytest.raises(NWSError) as caught:
        nws_wwa.get_all()
    assert len(recorder.urls) == 4
    assert caught.value.status_code == 502
    assert caught.value.url == recorder.urls[0]
    assert "502" in str(caught.value)


def test_network_failure_is_an_nws_error(monkeypatch):
    """A connection that never works raises NWSError, not a requests error."""
    use(monkeypatch, Recorder(requests.ConnectionError("no route")))
    with pytest.raises(NWSError, match="Could not reach NWS"):
        nws_wwa.get_hazards()


def test_missing_file_fails_at_once(monkeypatch):
    """A 404 is not worth another try."""
    recorder = use(monkeypatch, Recorder(FakeResponse(status_code=404)))
    with pytest.raises(NWSError) as caught:
        nws_wwa.get_all()
    assert len(recorder.urls) == 1
    assert caught.value.status_code == 404


def test_other_request_errors_are_wrapped(monkeypatch):
    """Other requests errors, such as a bad address, fail at once as NWSError."""
    recorder = use(monkeypatch, Recorder(requests.exceptions.InvalidURL("bad")))
    with pytest.raises(NWSError, match="failed"):
        nws_wwa.get_all()
    assert len(recorder.urls) == 1


def test_single_try_is_allowed(monkeypatch):
    """Asking for one try, or none, still makes one attempt."""
    recorder = use(monkeypatch, Recorder(FakeResponse(status_code=500)))
    with pytest.raises(NWSError):
        fetch.download_file("current_all.tar.gz", tries=0)
    assert len(recorder.urls) == 1


def test_verbose_prints_to_stderr(monkeypatch, good, capsys):
    """Each request is announced on standard error and nothing on standard output."""
    use(monkeypatch, Recorder(requests.ConnectionError("x"), good))
    nws_wwa.get_warnings(verbose=True)
    captured = capsys.readouterr()
    assert captured.err.count("Requesting https://tgftp.nws.noaa.gov/") == 2
    assert captured.out == ""


@pytest.mark.parametrize(
    "content,message",
    [
        (b"<html>not an archive</html>", "could not be read"),
        (b"", "could not be read"),
    ],
)
def test_garbage_is_a_data_error(monkeypatch, content, message):
    """A reply that is not a tar.gz raises NWSDataError."""
    use(monkeypatch, Recorder(FakeResponse(content)))
    with pytest.raises(NWSDataError, match=message):
        nws_wwa.get_all()


def test_archive_without_a_shapefile_is_a_data_error(monkeypatch, tmp_path):
    """A tar.gz with no .shp inside is rejected."""
    import io
    import tarfile

    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        info = tarfile.TarInfo("readme.txt")
        info.size = 2
        tar.addfile(info, io.BytesIO(b"hi"))
    use(monkeypatch, Recorder(FakeResponse(buffer.getvalue())))
    with pytest.raises(NWSDataError, match="no shapefile"):
        nws_wwa.get_all()


def test_unreadable_shapefile_is_a_data_error(monkeypatch):
    """A tar.gz whose .shp is not a shapefile raises NWSDataError."""
    import io
    import tarfile

    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        info = tarfile.TarInfo("current_all.shp")
        info.size = 4
        tar.addfile(info, io.BytesIO(b"nope"))
    use(monkeypatch, Recorder(FakeResponse(buffer.getvalue())))
    with pytest.raises(NWSDataError):
        nws_wwa.get_all()


def test_data_error_is_a_value_error_and_an_nws_error():
    """Old code that caught ValueError still works, and so does catching NWSError."""
    assert issubclass(NWSDataError, ValueError)
    assert issubclass(NWSDataError, NWSError)


def test_unreadable_record_is_a_data_error(fake_nws, monkeypatch):
    """A row that cannot be read as a record raises NWSDataError."""
    from nws_wwa import records

    def broken(feature):
        raise ValueError("bad row")

    monkeypatch.setattr(records.Alert, "from_feature", staticmethod(broken))
    with pytest.raises(NWSDataError, match="bad row"):
        nws_wwa.get_alert_records("warnings")
