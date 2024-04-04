# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [unreleased]

### Changed

- TeraChem `parse_git_commit` updated to `parse_version_control_details` to accommodate older versions of TeraChem compiled from the `Hg` days.

### Removed

- TeraChem `parse_version` parser. It was unused given the switch to only parsing `SinglePointResults` objects and not `Provenance` objects as well. The `parse_version_string` function is used by `qcop` to get the version of the program. We do not need to set the version of the program at `SinglePointResults.extras.program_version` anymore.

## [0.5.2] - 2023-09-27

### Removed

- All input parsing details from the library.

### Added

- `encode` top level function and encoder for TeraChem input files.

### Changed

- Added `FileType.stdout` as default `filetype` argument to `parse` decorator to reduce boilerplate in parsers.

## [0.5.1] - 2023-09-19

### Changed

- Dropped Python dependency from `^3.8.1` to `^3.8`. Can't remember what older dependency required `3.8.1` but it's not needed anymore.

## [0.5.0] - 2023-08-31

### Changed

- Updated `pydantic` from `v1` -> `v2`.

## [0.4.1] - 2023-07-19

### Changed

- Updated `qcio` from `0.3.0` -> `0.4.0`.

## [0.4.0] - 2023-07-17

### Changed

- Updated to used `qcio>=0.3.0` flattened models and the `SinglePointResults`object.

## [0.3.2] - 2023-06-29

### Fixed

- Updated package description in pyproject.toml from TeraChem specific parsing and MolSSI to all QC packages and qcio.

## [0.3.1] - 2023-06-29

### Added

- Git commit parsing for TeraChem as part of version parsing

### Changed

- `qcio` `>=0.1.0` -> `>=0.2.0`

## [0.3.0] - 2023-06-28

### Changed

- Dropped support for `QCSchema` models and changed to [qcio](https://github.com/coltonbh/qcio) data models.
- `parse` function now raises `NotImplementedError` and the default use case is to use `parse_computed_prop` instead and ignore inputs and provenance data. This is the minimum spec since QC programs can be powered using structured inputs and [qcop](https://github.com/coltonbh/qcop). I may go back to parsing entire `SinglePointSuccess/FailedOutput` objects if use cases arise.

## [0.2.1] - 2023-03-25

### Changed

- Generalized `CUDA error:` regex to catch all CUDA errors.

## [0.2.0] - 2023-03-24

### Added

- `cli` interface for parsing TeraChem outputs from the command line.
- `parse_natoms`, `parse_nmo`, `parse_total_charge`, `parse_spin_multiplicity`

### Removed

- Removed Hessian matrix dimension checking from `parse_hessian`. Dimension validation is already done via `pydantic` on the `AtomicResult` object.

## [0.1.0] - 2023-03-23

### Added

- Basic parsers for energy, gradient, Hessian (frequencies) calculations.
- Can return either `AtomicResult` or `FailedOperation` objects depending on whether calculation succeeded or failed.
- Tests for all parsers and the main `parse` function.

[unreleased]: https://github.com/coltonbh/qcparse/compare/0.5.2...HEAD
[0.5.2]: https://github.com/coltonbh/qcparse/releases/tag/0.5.2
[0.5.1]: https://github.com/coltonbh/qcparse/releases/tag/0.5.1
[0.5.0]: https://github.com/coltonbh/qcparse/releases/tag/0.5.0
[0.4.1]: https://github.com/coltonbh/qcparse/releases/tag/0.4.1
[0.4.0]: https://github.com/coltonbh/qcparse/releases/tag/0.4.0
[0.3.2]: https://github.com/coltonbh/qcparse/releases/tag/0.3.2
[0.3.1]: https://github.com/coltonbh/qcparse/releases/tag/0.3.1
[0.3.0]: https://github.com/coltonbh/qcparse/releases/tag/0.3.0
[0.2.1]: https://github.com/coltonbh/qcparse/releases/tag/0.2.1
[0.2.0]: https://github.com/coltonbh/qcparse/releases/tag/0.2.0
[0.1.0]: https://github.com/coltonbh/qcparse/releases/tag/0.1.0
