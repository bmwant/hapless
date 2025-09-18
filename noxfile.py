import nox

POETRY_EXEC = "poetry1.8"
TARGET_VERSIONS = ["3.8", "3.9", "3.10", "3.11", "3.12", "3.13", "3.14"]


@nox.session(python=TARGET_VERSIONS)
def test(session: nox.Session) -> None:
    # session.install(".")
    session.install(".[dev]")
    session.run("pytest", "tests")


@nox.session(python=TARGET_VERSIONS)
def check_python(session: nox.Session) -> None:
    session.run("python", "--version")
