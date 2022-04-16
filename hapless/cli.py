import shlex
from typing import Optional

import click

from hapless.main import Hapless


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
    h = Hapless()
    if hap_alias is not None:
        hap = h.get_hap(hap_alias)
        h.show(hap)
    else:
        haps = h.get_haps()
        h.stats(haps)


@cli.command()
@click.argument("hap_alias", metavar="hap")
def logs(hap_alias):
    h = Hapless()
    hap = h.get_hap(hap_alias)
    h.show(hap)


@cli.command()
def clean():
    pass


@cli.command()
@click.argument("cmd", nargs=-1)
def run(cmd):
    h = Hapless()
    h.run(shlex.join(cmd))


if __name__ == "__main__":
    cli()
