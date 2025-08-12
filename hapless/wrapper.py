import click

from hapless import Status
from hapless.cli_utils import get_or_exit, hap_argument, hapless


@click.group(invoke_without_command=True)
@hap_argument
def wrap_hap(hap_alias: str) -> None:
    hap = get_or_exit(hap_alias)
    if hap.status != Status.UNBOUND:
        with open(hap.stderr_path, "a") as f:
            f.write(f"Hap {hap} has to be unbound, found instead {hap.status}\n")
        return
    hapless._wrap_subprocess(hap)


if __name__ == "__main__":
    wrap_hap()
