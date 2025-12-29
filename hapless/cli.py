import sys
from shlex import join as shlex_join
from typing import Optional, Tuple

import click

from hapless import config
from hapless.cli_utils import (
    console,
    get_or_exit,
    hap_argument,
    hap_argument_optional,
    hapless,
)
from hapless.formatters import JSONFormatter, TableFormatter
from hapless.hap import Status
from hapless.utils import isatty, logger, validate_signal


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
def logs(hap_alias: str, follow: bool, stderr: bool):
    hap = get_or_exit(hap_alias)
    hapless.logs(hap, stderr=stderr, follow=follow)


@cli.command(short_help="Output error logs for a hap.")
@hap_argument
@click.option(
    "-f",
    "--follow",
    is_flag=True,
    default=False,
    help="Print new log lines as they are added.",
)
def errors(hap_alias: str, follow: bool):
    """
    Output stderr logs for a hap. Same as running `logs -e` command.
    """
    hap = get_or_exit(hap_alias)
    hapless.logs(hap, stderr=True, follow=follow)


@cli.command(short_help="Remove successfully completed haps.")
@click.option(
    "-a",
    "--all",
    "clean_all",
    is_flag=True,
    default=False,
    help="Include failed haps for the removal.",
)
def clean(clean_all: bool):
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
def run(cmd: Tuple[str, ...], name: str, check: bool):
    hap = hapless.get_hap(name)
    if hap is not None:
        console.error(f"Hap with such name already exists: {hap}")
        return sys.exit(1)

    # NOTE: click doesn't like `required` property for `cmd` argument
    # https://click.palletsprojects.com/en/latest/arguments/#variadic-arguments
    cmd_escaped = shlex_join(cmd).strip()
    if not cmd_escaped:
        console.error("You have to provide a command to run")
        return sys.exit(1)
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
def kill(hap_alias: Optional[str], killall: bool):
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
        # NOTE: `hap_alias` is guaranteed not to be None here
        hap = get_or_exit(hap_alias)  # ty: ignore[invalid-argument-type]
        hapless.kill([hap])


@cli.command(short_help="Send an arbitrary signal to a hap.")
@hap_argument
@click.argument("signal", callback=validate_signal, metavar="signal-code")
def signal(hap_alias: str, signal):
    hap = get_or_exit(hap_alias)
    hapless.signal(hap, signal)


@cli.command(short_help="Kill the hap and start it again.")
@hap_argument
def restart(hap_alias: str):
    hap = get_or_exit(hap_alias)
    hapless.restart(hap)


@cli.command(short_help="Set new name/alias for the existing hap.")
@hap_argument
@click.argument("new_name", metavar="new-name", required=True)
def rename(hap_alias: str, new_name: str):
    hap = get_or_exit(hap_alias)
    same_name_hap = hapless.get_hap(new_name)
    if same_name_hap is not None:
        console.print(f"Hap with such name already exists: {same_name_hap}")
        return sys.exit(1)
    hapless.rename_hap(hap, new_name)


@cli.command("__internal_wrap_hap", hidden=True)
@hap_argument
def _wrap_hap(hap_alias: str) -> None:
    if isatty() and not config.DEBUG:
        logger.critical("Internal command is not supposed to be run manually")
        return sys.exit(1)

    hap = get_or_exit(hap_alias)
    if hap.status != Status.UNBOUND:
        message = f"Hap {hap} has to be unbound, found instead {str(hap.status)}\n"
        with open(hap.stderr_path, "a") as f:
            f.write(message)
        logger.error(message)
        return sys.exit(1)

    hapless._wrap_subprocess(hap)


if __name__ == "__main__":
    cli()
