## hapless

![Checks](https://github.com/bmwant/hapless/actions/workflows/tests.yml/badge.svg)
[![PyPI](https://img.shields.io/pypi/v/hapless)](https://pypi.org/project/hapless/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/hapless)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
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

### Support project, support 🇺🇦 Ukraine!

🐶 `D7DA74qzZUyh9cctCxWovPTEovUSjGzL2S` this is [Dogecoin](https://dogecoin.com/) wallet to support the project.

🇺🇦 All donations will go towards supporting Ukraine in the war.

✉️ [Contact author](mailto:bmwant@gmail.com) directly in case you want to donate with some different payment option or check what has already been done.
