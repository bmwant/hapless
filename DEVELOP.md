### Development

Install [Poetry](https://python-poetry.org/) and project's dependencies

```bash
poetry install
```

Add new feature and launch tests

```bash
poetry run pytest -sv tests
# or
make tests
```

Lint the code and run type checking

```bash
make lint
make ty
```

Install git hooks for the automatic linting and code formatting with [pre-commit](https://pre-commit.com/)

```bash
pre-commit install
pre-commit run --all-files  # to initialize for the first time
pre-commit run ruff-check  # run a hook individually
```

Enable extra logging

```bash
export HAPLESS_DEBUG=1
```

Check coverage

```bash
poetry run pytest --cov=hapless --cov-report=html tests/
# or
make coverage-report
```

Run against multiple Python versions with [nox](https://nox.thea.codes/en/stable/index.html)

```bash
# Use uv as a default backend for virtual environment creation
export NOX_DEFAULT_VENV_BACKEND=uv

# Show available nox sessions
nox --list

# Check all of the defined Python versions are available
nox -s check_versions

# Run tests against all versions
nox -s test
```

### Releasing

Bump a version with features you want to include and build a package

```bash
poetry version patch  # patch version update
poetry version minor
poetry version major  # choose one based on semver rules
poetry build
```

Building and uploading package to PyPI is done automatically by GitHub workflow on tag creating

```bash
make tag
```
