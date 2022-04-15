import shlex
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
    # todo: show status for individual hap
    _status()


def _status():
    h = Hapless()
    haps = h.get_haps()
    h.stats(haps)



@cli.command()
def clean():
    pass


@cli.command()
@click.argument('cmd', nargs=-1)
def run(cmd):
    h = Hapless()
    print(f'This is: {cmd}')
    h.run(shlex.join(cmd))



if __name__ == '__main__':
    cli()
