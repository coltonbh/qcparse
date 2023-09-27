# qcparse

A library for parsing Quantum Chemistry output files into structured data objects and converting structured input objects into program-native input files. Uses data structures from [qcio](https://github.com/coltonbh/qcio).

[![image](https://img.shields.io/pypi/v/qcparse.svg)](https://pypi.python.org/pypi/qcparse)
[![image](https://img.shields.io/pypi/l/qcparse.svg)](https://pypi.python.org/pypi/qcparse)
[![image](https://img.shields.io/pypi/pyversions/qcparse.svg)](https://pypi.python.org/pypi/qcparse)
[![Actions status](https://github.com/coltonbh/qcparse/workflows/Tests/badge.svg)](https://github.com/coltonbh/qcparse/actions)
[![Actions status](https://github.com/coltonbh/qcparse/workflows/Basic%20Code%20Quality/badge.svg)](https://github.com/coltonbh/qcparse/actions)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v1.json)](https://github.com/charliermarsh/ruff)

`qcparse` works in harmony with a suite of other quantum chemistry tools for fast, structured, and interoperable quantum chemistry.

## The QC Suite of Programs

- [qcio](https://github.com/coltonbh/qcio) - Beautiful and user friendly data structures for quantum chemistry.
- [qcparse](https://github.com/coltonbh/qcparse) - A library for efficient parsing of quantum chemistry data into structured `qcio` objects and conversion of `qcio` input objects to program-native input files.
- [qcop](https://github.com/coltonbh/qcop) - A package for operating quantum chemistry programs using `qcio` standardized data structures. Compatible with `TeraChem`, `psi4`, `QChem`, `NWChem`, `ORCA`, `Molpro`, `geomeTRIC` and many more.
- [BigChem](https://github.com/mtzgroup/bigchem) - A distributed application for running quantum chemistry calculations at scale across clusters of computers or the cloud. Bring multi-node scaling to your favorite quantum chemistry program.
- `ChemCloud` - A [web application](https://github.com/mtzgroup/chemcloud-server) and associated [Python client](https://github.com/mtzgroup/chemcloud-client) for exposing a BigChem cluster securely over the internet.

## ✨ Basic Usage

- Installation:

  ```sh
  python -m pip install qcparse
  ```

- Parse a file into a `SinglePointResults` object with a single line of code.

  ```python
  from qcparse import parse
  # May pass a path or the contents of a file as string/bytes
  results = parse("terachem", "/path/to/stdout.log")
  ```

- The `results` object will be a `qcio.SinglePointResults` object. Run `dir(results)` inside a Python interpreter to see the various values you can access. A few prominent values are shown here as an example:

  ```python
  from qcparse import parse

  results = parse("/path/to/tc.out", "terachem")

  results.energy
  results.gradient # If a gradient calc
  results.hessian # If a hessian calc

  results.calcinfo_nmo # Number of molecular orbitals
  ```

- Parsed values can be written to disk like this:

  ```py
  with open("results.json", "w") as f:
      f.write(result.model_dumps_json())
  ```

- And read from disk like this:

  ```py
  from qcio import SinglePointResults

  results = SinglePointResults.open("results.json")
  ```

- You can also run `qcparse` from the command line like this:

  ```sh
  qcparse -h # Get help message for cli

  qcparse terachem ./path/to/tc.out > results.json # Parse TeraChem stdout to json
  ```

## 💻 Contributing

Please see the [contributing guide](./CONTRIBUTING.md) for details on how to contribute new parsers to this project :)

If there's data you'd like parsed from output files or want to support input files for a new program, please open an issue in this repo explaining the data items you'd like parsed and include an example output file containing the data, like [this](https://github.com/coltonbh/qcparse/issues/2).
