# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Available sections are:

-   `Added` for new features.
-   `Changed` for changes in existing functionality.
-   `Deprecated` for soon-to-be removed features.
-   `Removed` for now removed features.
-   `Fixed` for any bug fixes.
-   `Security` in case of vulnerabilities.


## [Unreleased]


## [v0.2.2]

### Changed

-   Upgrade [rich](https://rich.readthedocs.io/en/latest/) library

## [v0.2.1]

### Changed

-   Replace [flake8](https://flake8.pycqa.org/en/latest/) linter with [ruff](https://beta.ruff.rs/docs/)

## [v0.2.0] - 2022-11-17

### Fixed

-   Status icon is showed for the hap details
-   Properly kill hap and its underlying processes

## [v0.1.10] - 2022-11-10

### Added

-   Attach `.whl` and `.tar.gz` package build artifacts on each Github release.

## [v0.1.9] - 2022-11-08

### Added

-   Use Github Actions workflow to automatically publish package to PyPI.

## [v0.1.8] - 2022-11-07

### Changed

-   Use same dot icon for the status with different colors styling. This fixes table alignment on iTerm2 (MacOS).

## [v0.1.7] - 2022-11-06

### Changed

-   Use [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) for changelog tracking.

## [v0.1.6] - 2022-11-05

### Changed

-   Do not allow creating haps with same alias.
-   Warn when empty command is provided.

## [v0.1.5] - 2022-05-23

### Added

-   Add command to kill specific hap / all active haps.
-   Allow sending arbitrary signals to the hap.

## [v0.1.4] - 2022-04-26

### Added

-   Add verbose mode for the main command.
-   Allow specifying custom name for the hap.

## [v0.1.3] - 2022-04-20

### Added

-   Add suspending/resuming functionality for running haps.
-   Add unittests to cover basic invocations.

### Fixed

-   Fix issue with checking for failures.
-   Fix Python 3.7 compatibility.

## [v0.1.2] - 2022-04-19

### Added

-   Display extra information for the verbose status command.

### Fixed

-   Fix issue with attaching to short-living processes.

## [v0.1.1] - 2022-04-18

### Added

-   Save environment for the hap.
-   Show environment in the verbose status mode.

## [v0.1.0] - 2022-04-17

### Changed

-   Initial release.

[Unreleased]: https://github.com/bmwant/hapless/compare/v0.2.0...HEAD

[v0.2.0]: https://github.com/bmwant/hapless/compare/v0.1.10...v0.2.0

[v0.1.10]: https://github.com/bmwant/hapless/compare/v0.1.9...v0.1.10

[v0.1.9]: https://github.com/bmwant/hapless/compare/v0.1.8...v0.1.9

[v0.1.8]: https://github.com/bmwant/hapless/compare/v0.1.7...v0.1.8

[v0.1.7]: https://github.com/bmwant/hapless/compare/v0.1.6...v0.1.7

[v0.1.6]: https://github.com/bmwant/hapless/compare/v0.1.5...v0.1.6

[v0.1.5]: https://github.com/bmwant/hapless/compare/v0.1.4...v0.1.5

[v0.1.4]: https://github.com/bmwant/hapless/compare/v0.1.3...v0.1.4

[v0.1.3]: https://github.com/bmwant/hapless/compare/v0.1.2...v0.1.3

[v0.1.2]: https://github.com/bmwant/hapless/compare/v0.1.1...v0.1.2

[v0.1.1]: https://github.com/bmwant/hapless/compare/v0.1.0...v0.1.1

[v0.1.0]: https://github.com/bmwant/hapless/compare/6a73ff26ed15485a5c28a6d6ffb1032b187f06e7...v0.1.0
