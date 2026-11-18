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
