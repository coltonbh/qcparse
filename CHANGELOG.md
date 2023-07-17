# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [unreleased]

### Changed

- Updated to used `qcio>=0.3.0` flattened models and the `SinglePointResults`object.

## [0.3.1]

### Fixed

- Updated package description in pyproject.toml from TeraChem specific parsing and MolSSI to all QC packages and qcio.

## [0.3.1]

### Added

- Git commit parsing for TeraChem as part of version parsing

### Changed

- `qcio` `>=0.1.0` -> `>=0.2.0`

## [0.3.0]

### Changed

- Dropped support for `QCSchema` models and changed to [qcio](https://github.com/coltonbh/qcio) data models.
- `parse` function now raises `NotImplementedError` and the default use case is to use `parse_computed_prop` instead and ignore inputs and provenance data. This is the minimum spec since QC programs can be powered using structured inputs and [qcop](https://github.com/coltonbh/qcop). I may go back to parsing entire `SinglePointSuccess/FailedOutput` objects if use cases arise.

## [0.2.1]

### Changed

- Generalized `CUDA error:` regex to catch all CUDA errors.

## [0.2.0]

### Added

- `cli` interface for parsing TeraChem outputs from the command line.
- `parse_natoms`, `parse_nmo`, `parse_total_charge`, `parse_spin_multiplicity`

### Removed

- Removed Hessian matrix dimension checking from `parse_hessian`. Dimension validation is already done via `pydantic` on the `AtomicResult` object.

## [0.1.0]

### Added

- Basic parsers for energy, gradient, Hessian (frequencies) calculations.
- Can return either `AtomicResult` or `FailedOperation` objects depending on whether calculation succeeded or failed.
- Tests for all parsers and the main `parse` function.

[unreleased]: https://github.com/coltonbh/qcparse/compare/0.3.2...HEAD
[0.3.2]: https://github.com/coltonbh/qcparse/releases/tag/0.3.2
[0.3.1]: https://github.com/coltonbh/qcparse/releases/tag/0.3.1
[0.3.0]: https://github.com/coltonbh/qcparse/releases/tag/0.3.0
[0.2.1]: https://github.com/coltonbh/qcparse/releases/tag/0.2.1
[0.2.0]: https://github.com/coltonbh/qcparse/releases/tag/0.2.0
[0.1.0]: https://github.com/coltonbh/qcparse/releases/tag/0.1.0
