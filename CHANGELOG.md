# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Available sections are:

* `Added` for new features.
* `Changed` for changes in existing functionality.
* `Deprecated` for soon-to-be removed features.
* `Removed` for now removed features.
* `Fixed` for any bug fixes.
* `Security` in case of vulnerabilities.

## [Unreleased]

### Changed

- Use [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) for changelog tracking.
## [0.1.6]

### Changed

* Do not allow creating haps with same alias
* Warn when empty command is provided


## [0.1.5]

### Added

* Add command to kill specific hap / all active haps
* Allow sending arbitrary signals to the hap


## [0.1.4]

### Added

* Add verbose mode for the main command
* Allow specifying custom name for the hap


## [0.1.3]

### Added

* Add suspending/resuming functionality for running haps
* Add unittests to cover basic invocations

### Fixed

* Fix issue with checking for failures
* Fix Python 3.7 compatibility


## [0.1.2]

### Added

* Display extra information for the verbose status command

### Fixed

* Fix issue with attaching to short-living processes


## [0.1.1]

### Added

* Save environment for the hap
* Show environment in the verbose status mode


## [0.1.0]

### Changed

* Initial release
