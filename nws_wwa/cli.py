"""The nwswwa command-line interface."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import click

from nws_wwa import NWSError, get_all, get_hazards, get_warnings
from nws_wwa.fetch import DEFAULT_TIMEOUT


def _common_options(func: Callable[..., Any]) -> Callable[..., Any]:
    """Add the options every download command shares.

    Args:
        func: The click command function to decorate.

    Returns:
        The same function with the timeout and verbose options attached.
    """
    decorators = [
        click.option(
            "--timeout",
            default=DEFAULT_TIMEOUT,
            show_default=True,
            type=click.FloatRange(min=1),
            help="Seconds to wait for NWS on each try",
        ),
        click.option("--verbose", is_flag=True, help="Print each request to stderr"),
    ]
    for decorator in reversed(decorators):
        func = decorator(func)
    return func


def _download(getter: Callable[..., Any], timeout: float, verbose: bool) -> None:
    """Download a feed and print it as GeoJSON.

    The GeoJSON is the only thing printed to standard output. The progress
    messages from ``--verbose`` go to standard error, so redirecting the output
    to a file never mixes them in.

    Args:
        getter: The function that downloads the feed, such as ``get_all``.
        timeout: Seconds to wait for NWS on each try.
        verbose: Whether to print each request to standard error.

    Raises:
        click.ClickException: If NWS cannot be reached or sends back something
            unreadable, so the command prints one line starting with "Error:"
            and exits with code 1.
    """
    try:
        data = getter(verbose=verbose, timeout=timeout)
    except NWSError as error:
        raise click.ClickException(str(error)) from error
    click.echo(data)


@click.group()
def cmd() -> None:
    """
    A command-line interface for downloading watch, warning and advisory data from the National Weather Service.

    Returns GeoJSON.
    """
    pass


@cmd.command(help="All watch, warning and advisory data")
@_common_options
def all(timeout, verbose):
    _download(get_all, timeout, verbose)


@cmd.command(help="All hazard data")
@_common_options
def hazards(timeout, verbose):
    _download(get_hazards, timeout, verbose)


@cmd.command(help="All warnings data")
@_common_options
def warnings(timeout, verbose):
    _download(get_warnings, timeout, verbose)


if __name__ == "__main__":
    cmd()
