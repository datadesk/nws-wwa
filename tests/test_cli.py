"""Offline tests of the nwswwa command line."""

import pytest
from click.testing import CliRunner

from nws_wwa.cli import cmd

from .conftest import DATA


@pytest.mark.parametrize("command", ["all", "hazards", "warnings"])
def test_output_is_unchanged(fake_nws, command):
    """Each command prints exactly the GeoJSON the first release printed.

    The expected files were made by the old code, before any upgrade work.
    """
    result = CliRunner().invoke(cmd, [command])
    assert result.exit_code == 0
    assert result.output == (DATA / f"expected_{command}.json").read_text()


def test_help_lists_the_commands():
    """The three original commands are still there."""
    result = CliRunner().invoke(cmd, ["--help"])
    assert result.exit_code == 0
    for command in ["all", "hazards", "warnings"]:
        assert command in result.output


def test_timeout_and_verbose_options(monkeypatch, sample):
    """--timeout goes to the request, and --verbose never touches the JSON."""
    from nws_wwa import fetch

    from .conftest import FakeResponse

    timeouts = []

    def get(url, *args, timeout=None, **kwargs):
        timeouts.append(timeout)
        return FakeResponse(sample("warnings"))

    monkeypatch.setattr(fetch.requests, "get", get)
    result = CliRunner().invoke(cmd, ["warnings", "--timeout", "7", "--verbose"])
    assert result.exit_code == 0
    assert timeouts == [7.0]
    assert result.stdout == (DATA / "expected_warnings.json").read_text()
    assert "Requesting https://tgftp.nws.noaa.gov/" in result.stderr


@pytest.mark.parametrize("command", ["all", "hazards", "warnings"])
def test_errors_print_one_line(monkeypatch, command):
    """When NWS is down the command prints one 'Error:' line and exits with 1."""
    from nws_wwa import fetch

    from .conftest import FakeResponse

    monkeypatch.setattr(
        fetch.requests, "get", lambda *a, **k: FakeResponse(status_code=503)
    )
    result = CliRunner().invoke(cmd, [command])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr.startswith("Error: NWS sent back status 503")
    assert "Traceback" not in result.stderr


def test_timeout_must_be_at_least_one():
    """A zero or negative timeout is refused."""
    result = CliRunner().invoke(cmd, ["all", "--timeout", "0"])
    assert result.exit_code == 2
