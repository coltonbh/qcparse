# qcparse

A library for parsing Quantum Chemistry output files into structured data objects. Uses data structures from [qcio](https://github.com/coltonbh/qcio).

[![image](https://img.shields.io/pypi/v/qcparse.svg)](https://pypi.python.org/pypi/qcparse)
[![image](https://img.shields.io/pypi/l/qcparse.svg)](https://pypi.python.org/pypi/qcparse)
[![image](https://img.shields.io/pypi/pyversions/qcparse.svg)](https://pypi.python.org/pypi/qcparse)
[![Actions status](https://github.com/coltonbh/qcparse/workflows/Tests/badge.svg)](https://github.com/coltonbh/qcparse/actions)
[![Actions status](https://github.com/coltonbh/qcparse/workflows/Basic%20Code%20Quality/badge.svg)](https://github.com/coltonbh/qcparse/actions)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v1.json)](https://github.com/charliermarsh/ruff)

## ☝️ NOTE

This package was originally designed to run as a standalone parser to generate `SinglePointOutput` and `ProgramFailure` objects parsing all input and provenance data in addition to computed output data; however, once [qcop](https://github.com/coltonbh/qcop) was built to power quantum chemistry programs the only parsing needed was for the simpler `SinglePointResults` values. There are still remnants of the original `parse` function in the repo and I've left them for now in case I find a use for the general purpose parsing.

## ✨ Basic Usage

- Installation:

  ```sh
  python -m pip install qcparse
  ```

- Parse a file into a `SinglePointResults` object with a single line of code.

  ```python
  from qcparse import parse_results

  results = parse_results("/path/to/tc.out", "terachem")
  ```

- The `results` object will be a `SinglePointResults` object. Run `dir(results)` inside a Python interpreter to see the various values you can access. A few prominent values are shown here as an example:

  ```python
  from qcparse import parse_results

  results = parse_results("/path/to/tc.out", "terachem")

  results.energy
  results.gradient # If a gradient calc
  results.hessian # If a hessian calc

  results.calcinfo_nmo # Number of molecular orbitals
  ```

- Parsed values can be written to disk like this:

  ```py
  with open("results.json", "w") as f:
      f.write(result.json())
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

If there's data you'd like parsed fromI output files, please open an issue in this repo explaining the data items you'd like parsed and include an example output file containing the data, like [this](https://github.com/coltonbh/qcparse/issues/2).

If you'd like to add a parser yourself see the docstring in `qcparse.parsers` for a primer and see the examples written in the module. Adding a parser for new data is quick and easy :)
