import sys
from typing import Optional

import click
from rich.console import Console

from hapless import config
from hapless.main import Hapless

try:
    from shlex import join as shlex_join
except ImportError:
    # Fallback for Python 3.7
    from hapless.utils import shlex_join_backport as shlex_join

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
@click.option("-v", "--verbose", is_flag=True, default=False)
@click.pass_context
def cli(ctx, verbose):
    if ctx.invoked_subcommand is None:
        _status(None, verbose=verbose)


@cli.command()
@click.argument("hap_alias", metavar="hap", required=False)
@click.option("-v", "--verbose", is_flag=True, default=False)
def status(hap_alias, verbose):
    _status(hap_alias, verbose)


@cli.command()
@click.argument("hap_alias", metavar="hap", required=False)
@click.option("-v", "--verbose", is_flag=True, default=False)
def show(hap_alias, verbose):
    _status(hap_alias, verbose)


def _status(hap_alias: Optional[str] = None, verbose: bool = False):
    if hap_alias is not None:
        hap = get_or_exit(hap_alias)
        hapless.show(hap, verbose=verbose)
    else:
        haps = hapless.get_haps()
        hapless.stats(haps, verbose=verbose)


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
@click.option("-n", "--name")
@click.option("--check", is_flag=True, default=False)
def run(cmd, name, check):
    hapless.run(shlex_join(cmd), name=name, check=check)


@cli.command()
@click.argument("hap_alias", metavar="hap")
def pause(hap_alias):
    hap = get_or_exit(hap_alias)
    hapless.pause_hap(hap)


@cli.command()
@click.argument("hap_alias", metavar="hap")
def resume(hap_alias):
    hap = get_or_exit(hap_alias)
    hapless.resume_hap(hap)


@cli.command()
@click.argument("hap_alias", metavar="hap", required=False)
@click.option("-a", "--all", "killall", is_flag=True, default=False)
def kill(hap_alias, killall):
    if hap_alias is not None and killall:
        raise click.BadOptionUsage(
            "killall", "Cannot use --all flag while hap id provided"
        )

    if hap_alias is None and not killall:
        raise click.BadArgumentUsage("Provide hap alias to kill")

    if killall:
        haps = hapless.get_haps()
        hapless.kill(haps)
    else:
        hap = get_or_exit(hap_alias)
        hapless.kill([hap])


if __name__ == "__main__":
    cli()
