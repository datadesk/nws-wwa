#! /usr/bin/env python
# -*- coding: utf-8 -*-
import click
from nws_wwa import (
    get_all,
    get_hazards,
    get_warnings
)


@click.group()
def cmd():
    """
    A command-line interface for downloading watch, warning and advisory data from the National Weather Service.
    Returns GeoJSON.
    """
    pass


@cmd.command(help="All watch, warning and advisory data")
def all():
    click.echo(get_all())


@cmd.command(help="All hazard data")
def hazards():
    click.echo(get_hazards())


@cmd.command(help="All warnings data")
def warnings():
    click.echo(get_warnings())


if __name__ == '__main__':
    cmd()
