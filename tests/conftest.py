"""Shared test setup that keeps the tests off the real NWS website."""

from pathlib import Path

import pytest

DATA = Path(__file__).parent / "data"


class FakeResponse:
    """A stand-in for a ``requests`` response."""

    def __init__(self, content: bytes = b"", status_code: int = 200) -> None:
        self.content = content
        self.status_code = status_code
        self.ok = status_code < 400


@pytest.fixture
def sample():
    """Return a function that reads a saved sample file as bytes.

    The samples in ``tests/data`` are small cuts of the real files NWS
    publishes, with the same columns and the same kinds of rows.
    """

    def read(name: str) -> bytes:
        return (DATA / f"sample_{name}.tar.gz").read_bytes()

    return read


@pytest.fixture
def fake_nws(monkeypatch, sample):
    """Replace ``requests.get`` and record the addresses asked for.

    The fake answers each request with the sample that matches the file name in
    the address, such as ``current_hazards.tar.gz``.
    """
    import nws_wwa

    class Fake:
        urls: list[str]

    fake = Fake()
    fake.urls = []

    def get(url, *args, **kwargs):
        fake.urls.append(url)
        name = url.rsplit("/", 1)[-1].removeprefix("current_").removesuffix(".tar.gz")
        return FakeResponse(sample(name))

    monkeypatch.setattr(nws_wwa.requests, "get", get)
    return fake
