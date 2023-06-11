## hapless

![Checks](https://github.com/bmwant/hapless/actions/workflows/tests.yml/badge.svg)
[![PyPI](https://img.shields.io/pypi/v/hapless)](https://pypi.org/project/hapless/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/hapless)


[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![EditorConfig](https://img.shields.io/badge/-EditorConfig-grey?logo=editorconfig)](https://editorconfig.org/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

> **hapless** (*adjective*) - (especially of a person) unfortunate. A developer who accidentally launched long-running process in the foreground.

Simplest way of running and tracking processes in the background.

[![asciicast](https://asciinema.org/a/489924.svg)](https://asciinema.org/a/489924?speed=2)

### Installation

```bash
$ pip install hapless

# or to make sure proper pip is used for the given python executable
$ python -m pip install hapless
```

Install into user-specific directory in case of any permissions-related issues.

```bash
$ pip install --user hapless
$ python -m pip install --user hapless
```

### Usage

```bash
# Run arbitrary script
$ hap run -- python long_running.py

# Show summary table
$ hap

# Display status of the specific process
$ hap status 1
```

See [USAGE.md](https://github.com/bmwant/hapless/blob/main/USAGE.md) for the complete list of commands and available parameters.

### Contribute

See [DEVELOP.md](https://github.com/bmwant/hapless/blob/main/DEVELOP.md) to setup your local development environment and feel free to create a pull request with a new feature.

### Releases

See [CHANGELOG.md](https://github.com/bmwant/hapless/blob/main/CHANGELOG.md) for the new features included within each release.

### See also

* [Rich](https://rich.readthedocs.io/en/stable/introduction.html) console UI library.
* [Supervisor](http://supervisord.org/) full-fledged process manager.
* [podmena](https://github.com/bmwant/podmena) provides nice emoji icons to commit messages.

### Support 🇺🇦 Ukraine in the war!

🇺🇦 Donate to [this foundation](https://prytulafoundation.org/en) in case you want to help. Every donation matter!
