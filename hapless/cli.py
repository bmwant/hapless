import sys
from typing import Optional

import click
from rich.console import Console

from hapless import config
from hapless.main import Hapless
from hapless.utils import validate_signal

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


@cli.command(short_help="Display information about haps")
@click.argument("hap_alias", metavar="hap", required=False)
@click.option("-v", "--verbose", is_flag=True, default=False)
def status(hap_alias, verbose):
    _status(hap_alias, verbose)


@cli.command(short_help="Same as a status")
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


@cli.command(short_help="Output logs for a hap")
@click.argument("hap_alias", metavar="hap")
@click.option("-f", "--follow", is_flag=True, default=False)
@click.option("-e", "--stderr", is_flag=True, default=False)
def logs(hap_alias, follow, stderr):
    hap = get_or_exit(hap_alias)
    hapless.logs(hap, stderr=stderr, follow=follow)


@cli.command(short_help="Remove finished haps")
@click.option("--skip-failed", is_flag=True, default=False)
def clean(skip_failed):
    hapless.clean(skip_failed)


@cli.command(short_help="Execute background command as a hap")
@click.argument("cmd", nargs=-1)
@click.option("-n", "--name")
@click.option("--check", is_flag=True, default=False)
def run(cmd, name, check):
    hap = hapless.get_hap(name)
    if hap is not None:
        console.print(
            f"{config.ICON_INFO} Hap with such name already exists: {hap}",
            style=f"{config.COLOR_ERROR} bold",
        )
        sys.exit(1)

    # NOTE: click doesn't like `required` property for `cmd` argument
    # https://click.palletsprojects.com/en/latest/arguments/#variadic-arguments
    cmd_escaped = shlex_join(cmd).strip()
    if not cmd_escaped:
        console.print(
            f"{config.ICON_INFO} You have to provide a command to run",
            style=f"{config.COLOR_ERROR} bold",
        )
        sys.exit(1)
    hapless.run(cmd_escaped, name=name, check=check)


@cli.command(short_help="Pause a specific hap")
@click.argument("hap_alias", metavar="hap")
def pause(hap_alias):
    hap = get_or_exit(hap_alias)
    hapless.pause_hap(hap)


@cli.command(short_help="Resume execution of a paused hap")
@click.argument("hap_alias", metavar="hap")
def resume(hap_alias):
    hap = get_or_exit(hap_alias)
    hapless.resume_hap(hap)


@cli.command(short_help="Terminate a specific hap / all haps")
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


@cli.command(short_help="Send an arbitrary signal to a hap")
@click.argument("hap_alias", metavar="hap")
@click.argument("signal", callback=validate_signal, metavar="signal-code")
def signal(hap_alias, signal):
    hap = get_or_exit(hap_alias)
    hapless.signal(hap, signal)


if __name__ == "__main__":
    cli()
