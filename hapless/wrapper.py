import click

from hapless import Status
from hapless.cli_utils import console, get_or_exit, hap_argument, hapless


@click.group(invoke_without_command=True)
@hap_argument
def wrap_hap(hap_alias: str) -> None:
    print("State is here:", hapless._hapless_dir)
    hap = get_or_exit(hap_alias)
    if hap.status != Status.UNBOUND:
        console.error(f"Hap {hap} is already bound to a process")
        return
    hapless._wrap_subprocess(hap)


if __name__ == "__main__":
    wrap_hap()
