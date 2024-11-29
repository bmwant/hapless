import nox

TARGET_VERSIONS = ["3.7", "3.8", "3.9", "3.10", "3.11", "3.12"]


@nox.session(python=TARGET_VERSIONS)
def test(session: nox.Session) -> None:
    # session.install("-e", ".[dev]")
    session.install(".")
    session.run("pytest", "tests")
