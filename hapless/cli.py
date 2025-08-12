import sys
from typing import Optional

import click

from hapless.cli_utils import (
    console,
    get_or_exit,
    hap_argument,
    hap_argument_optional,
    hapless,
)
from hapless.formatters import JSONFormatter, TableFormatter
from hapless.utils import validate_signal

try:
    from shlex import join as shlex_join
except ImportError:
    # Fallback for Python 3.7
    from hapless.utils import shlex_join_backport as shlex_join


@click.group(invoke_without_command=True)
@click.version_option(message="hapless, version %(version)s")
@click.option("-v", "--verbose", is_flag=True, default=False)
@click.option(
    "--json", "json_output", is_flag=True, default=False, help="Output in JSON format."
)
@click.pass_context
def cli(ctx, verbose: bool, json_output: bool):
    if ctx.invoked_subcommand is None:
        _status(None, verbose=verbose, json_output=json_output)


@cli.command(short_help="Display information about haps.")
@hap_argument_optional
@click.option("-v", "--verbose", is_flag=True, default=False)
@click.option(
    "--json", "json_output", is_flag=True, default=False, help="Output in JSON format."
)
def status(hap_alias: Optional[str], verbose: bool, json_output: bool):
    _status(hap_alias, verbose, json_output=json_output)


@cli.command(short_help="Same as a status.")
@hap_argument_optional
@click.option("-v", "--verbose", is_flag=True, default=False)
@click.option(
    "--json", "json_output", is_flag=True, default=False, help="Output in JSON format."
)
def show(hap_alias: Optional[str], verbose: bool, json_output: bool):
    _status(hap_alias, verbose, json_output=json_output)


def _status(
    hap_alias: Optional[str] = None,
    verbose: bool = False,
    json_output: bool = False,
):
    formatter_cls = JSONFormatter if json_output else TableFormatter
    formatter = formatter_cls(verbose=verbose)
    if hap_alias is not None:
        hap = get_or_exit(hap_alias)
        hapless.show(hap, formatter=formatter)
    else:
        haps = hapless.get_haps(accessible_only=False)
        hapless.stats(haps, formatter=formatter)


@cli.command(short_help="Output logs for a hap.")
@hap_argument
@click.option("-f", "--follow", is_flag=True, default=False)
@click.option("-e", "--stderr", is_flag=True, default=False)
def logs(hap_alias: str, follow, stderr):
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
    hapless.run_command(cmd_escaped, name=name, check=check)


@cli.command(short_help="Pause a specific hap.")
@hap_argument
def pause(hap_alias: str):
    hap = get_or_exit(hap_alias)
    hapless.pause_hap(hap)


@cli.command(short_help="Resume execution of a paused hap.")
@hap_argument
def resume(hap_alias: str):
    hap = get_or_exit(hap_alias)
    hapless.resume_hap(hap)


@cli.command(short_help="Terminate a specific hap / all haps.")
@hap_argument_optional
@click.option("-a", "--all", "killall", is_flag=True, default=False)
def kill(hap_alias: Optional[str], killall):
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
@hap_argument
@click.argument("signal", callback=validate_signal, metavar="signal-code")
def signal(hap_alias: str, signal):
    hap = get_or_exit(hap_alias)
    hapless.signal(hap, signal)


@cli.command(short_help="Kills the hap and starts it again.")
@hap_argument
def restart(hap_alias: str):
    hap = get_or_exit(hap_alias)
    hapless.restart(hap)


@cli.command(short_help="Sets new name/alias for the existing hap.")
@hap_argument
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
