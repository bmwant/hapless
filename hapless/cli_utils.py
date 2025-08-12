import sys

import click

from hapless import Hap, Hapless, config

hapless = Hapless(hapless_dir=config.HAPLESS_DIR)
console = hapless.ui


def get_or_exit(hap_alias: str) -> Hap:
    hap = hapless.get_hap(hap_alias)
    if hap is None:
        console.error(f"No such hap: {hap_alias}")
        sys.exit(1)
    if not hap.accessible:
        console.error(f"Cannot manage hap launched by another user. Owner: {hap.owner}")
        sys.exit(1)
    return hap


hap_argument = click.argument(
    "hap_alias",
    metavar="hap",
    required=True,
)
hap_argument_optional = click.argument(
    "hap_alias",
    metavar="hap",
    required=False,
)
