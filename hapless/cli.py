import click


@click.group()
@click.version_option(message="hapless, version %(version)s")
def cli():
    pass
