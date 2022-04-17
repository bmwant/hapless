import shlex
import sys
from typing import Optional

import click
from rich.console import Console

from hapless import config
from hapless.main import Hapless

console = Console(highlight=False)
hapless = Hapless()


def get_or_exit(hap_alias: str):
    hap = hapless.get_hap(hap_alias)
    if hap is None:
        console.print(
            f"{config.ICON_INFO} No such hap: {hap_alias}",
            style=f"{config.COLOR_ERROR} bold",
        )
        sys.exit(1)
    return hap


@click.group(invoke_without_command=True)
@click.version_option(message="hapless, version %(version)s")
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        _status()


@cli.command()
@click.argument("hap_alias", metavar="hap", required=False)
def status(hap_alias):
    _status(hap_alias)


@cli.command()
@click.argument("hap_alias", metavar="hap", required=False)
def show(hap_alias):
    _status(hap_alias)


def _status(hap_alias: Optional[str] = None):
    if hap_alias is not None:
        hap = get_or_exit(hap_alias)
        hapless.show(hap)
    else:
        haps = hapless.get_haps()
        hapless.stats(haps)


@cli.command()
@click.argument("hap_alias", metavar="hap")
@click.option("-f", "--follow", is_flag=True, default=False)
def logs(hap_alias, follow):
    hap = get_or_exit(hap_alias)
    hapless.logs(hap, follow=follow)


@cli.command()
@click.option("--skip-failed", is_flag=True, default=False)
def clean(skip_failed):
    hapless.clean(skip_failed)


@cli.command()
@click.argument("cmd", nargs=-1)
@click.option("--check", is_flag=True, default=False)
def run(cmd, check):
    hapless.run(shlex.join(cmd), check=check)


if __name__ == "__main__":
    cli()
