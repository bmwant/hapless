import re
import subprocess

import nox

POETRY_EXEC = "poetry1.8"
TARGET_VERSIONS = ["3.8", "3.9", "3.10", "3.11", "3.12", "3.13"]


def poetry_python_versions():
    """Return all Python versions and their interpreter paths from Poetry envs."""
    output = subprocess.check_output(
        [POETRY_EXEC, "env", "list", "--full-path"], text=True
    )
    envs = []
    for line in output.splitlines():
        line = re.sub(r"\s*\(Activated\)", "", line.strip())
        envs.append("{}/bin/python".format(line))
    return envs


# NOTE: create environments with poetry before nox invocation
TARGET_VERSIONS_AVAILABLE = poetry_python_versions()


@nox.session(python=TARGET_VERSIONS_AVAILABLE)
def test(session: nox.Session) -> None:
    # session.install(".")
    session.install(".[dev]")
    session.run("pytest", "tests")


@nox.session(python=TARGET_VERSIONS_AVAILABLE)
def check_python(session: nox.Session) -> None:
    session.run("python", "--version")


if __name__ == "__main__":
    print(poetry_python_versions())
