import sys
import shlex, subprocess
import click

from hapless.main import Hapless


@click.group(invoke_without_command=True)
@click.version_option(message="hapless, version %(version)s")
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        _status()


@cli.command()
def status():
    _status()


def _status():
    h = Hapless()
    haps = h.get_haps()
    h.stats(haps)


@cli.command()
def run():
    h = Hapless()
    h.run('python long_running.py')


if __name__ == '__main__':
    cli()
