import sys
from typing import Optional

import click

from hapless import config
from hapless.main import Hapless
from hapless.utils import validate_signal

try:
    from shlex import join as shlex_join
except ImportError:
    # Fallback for Python 3.7
    from hapless.utils import shlex_join_backport as shlex_join

hapless = Hapless(hapless_dir=config.HAPLESS_DIR)
console = hapless.ui


def get_or_exit(hap_alias: str):
    hap = hapless.get_hap(hap_alias)
    if hap is None:
        console.error(f"No such hap: {hap_alias}")
        sys.exit(1)
    if not hap.accessible:
        console.error(f"Cannot manage hap launched by another user. Owner: {hap.owner}")
        sys.exit(1)
    return hap


@click.group(invoke_without_command=True)
@click.version_option(message="hapless, version %(version)s")
@click.option("-v", "--verbose", is_flag=True, default=False)
@click.pass_context
def cli(ctx, verbose):
    if ctx.invoked_subcommand is None:
        _status(None, verbose=verbose)


@cli.command(short_help="Display information about haps.")
@click.argument("hap_alias", metavar="hap", required=False)
@click.option("-v", "--verbose", is_flag=True, default=False)
def status(hap_alias, verbose):
    _status(hap_alias, verbose)


@cli.command(short_help="Same as a status.")
@click.argument("hap_alias", metavar="hap", required=False)
@click.option("-v", "--verbose", is_flag=True, default=False)
def show(hap_alias, verbose):
    _status(hap_alias, verbose)


def _status(hap_alias: Optional[str] = None, verbose: bool = False):
    if hap_alias is not None:
        hap = get_or_exit(hap_alias)
        hapless.show(hap, verbose=verbose)
    else:
        haps = hapless.get_haps(accessible_only=False)
        hapless.stats(haps, verbose=verbose)


@cli.command(short_help="Output logs for a hap.")
@click.argument("hap_alias", metavar="hap")
@click.option("-f", "--follow", is_flag=True, default=False)
@click.option("-e", "--stderr", is_flag=True, default=False)
def logs(hap_alias, follow, stderr):
    hap = get_or_exit(hap_alias)
    hapless.logs(hap, stderr=stderr, follow=follow)


@cli.command(short_help="Remove successfully completed haps.")
@click.option(
    "-a",
    "--all",
    "clean_all",
    is_flag=True,
    default=False,
    help="Include failed haps for the removal.",
)
def clean(clean_all):
    hapless.clean(clean_all=clean_all)


@cli.command(short_help="Remove all finished haps, including failed ones.")
def cleanall():
    hapless.clean(clean_all=True)


@cli.command(
    short_help="Execute background command as a hap.",
    context_settings=dict(
        ignore_unknown_options=True,
    ),
)
@click.argument("cmd", nargs=-1)
@click.option(
    "-n", "--name", help="Provide your own alias for the hap instead of a default one."
)
@click.option(
    "--check",
    is_flag=True,
    default=False,
    help="Verify command launched does not fail immediately.",
)
def run(cmd, name, check):
    hap = hapless.get_hap(name)
    if hap is not None:
        console.error(f"Hap with such name already exists: {hap}")
        sys.exit(1)

    # NOTE: click doesn't like `required` property for `cmd` argument
    # https://click.palletsprojects.com/en/latest/arguments/#variadic-arguments
    cmd_escaped = shlex_join(cmd).strip()
    if not cmd_escaped:
        console.error("You have to provide a command to run")
        sys.exit(1)
    hapless.run(cmd_escaped, name=name, check=check)


@cli.command(short_help="Pause a specific hap.")
@click.argument("hap_alias", metavar="hap")
def pause(hap_alias):
    hap = get_or_exit(hap_alias)
    hapless.pause_hap(hap)


@cli.command(short_help="Resume execution of a paused hap.")
@click.argument("hap_alias", metavar="hap")
def resume(hap_alias):
    hap = get_or_exit(hap_alias)
    hapless.resume_hap(hap)


@cli.command(short_help="Terminate a specific hap / all haps.")
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


@cli.command(short_help="Send an arbitrary signal to a hap.")
@click.argument("hap_alias", metavar="hap")
@click.argument("signal", callback=validate_signal, metavar="signal-code")
def signal(hap_alias, signal):
    hap = get_or_exit(hap_alias)
    hapless.signal(hap, signal)


@cli.command(short_help="Kills the hap and starts it again.")
@click.argument("hap_alias", metavar="hap", required=True)
def restart(hap_alias):
    hap = get_or_exit(hap_alias)
    hapless.restart(hap)


@cli.command(short_help="Sets new name/alias for the existing hap.")
@click.argument("hap_alias", metavar="hap", required=True)
@click.argument("new_name", metavar="new-name", required=True)
def rename(hap_alias: str, new_name: str):
    hap = get_or_exit(hap_alias)
    same_name_hap = hapless.get_hap(new_name)
    if same_name_hap is not None:
        console.print(f"Hap with such name already exists: {same_name_hap}")
        sys.exit(1)
    hapless.rename_hap(hap, new_name)


if __name__ == "__main__":
    cli()
