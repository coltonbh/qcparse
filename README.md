# tcparse

A library for parsing TeraChem output files into structured MolSSI data objects.

## ✨ Basic Usage

- Installation:

  ```sh
  python -m pip install tcparse
  ```

- Parse files into `AtomicResult` or `FailedOperation` objects with a single line of code.

  ```python
  from tcparse import parse

  result = parse("/path/to/tc.out")
  ```

- If your `xyz` file no longer exists where `tc.out` specifies (the `XYZ coordinates` line), `parse` will raise a `FileNotFoundError`. You can pass `ignore_xyz=True` and `parse` will use a dummy hydrogen molecule instead. The correct values from `tc.out` will be parsed; however, `result.molecule` will be the dummy hydrogen.

  ```python
  from tcparse import parse

  result = parse("/path/to/tc.out", ignore_xyz=True)
  print(result) # Real results from tc.out
  print(result.molecule) # Dummy hydrogen molecule
  ```

- The `result` object will be either an `AtomicResult` or `FailedOperation`. Run `dir(result)` inside a Python interpreter to see the various values you can access. A few prominent values are shown here as an example:

  ```python
  from tcparse import parse

  result = parse("/path/to/tc.out")

  if result.success:
      # result is AtomicResult
      result.driver # "energy", "gradient", or "hessian"
      result.model # Method and basis
      result.return_result # Core value from the computation. Will be either energy or grad/Hess matrix
      result.properties # Collection of computed properties. Two shown below.
      result.properties.return_energy # Available for all calcs
      result.properties.return_gradient # Available for grad/Hess calcs
      result.molecule # The molecule used for the computation
      result.stdout # The full TeraChem stdout
      result.provenance # Provenance data for the computation (TeraChem version)
  else:
      # result is FailedOperation
      result.error # ComputeError object describing error
      result.input_data # Basic data about the inputs supplied, does NOT include keywords
      result.error.error_message # Parsed error message from TeraChem stdout
      result.error.extras['stdout'] # Full TeraChem stdout
  ```

- Parsed results can be written to disk like this:

  ```py
  with open("myresult.json", "w") as f:
      f.write(result.json())
  ```

- And read from disk like this:

  ```py
  from qcelemental.models import AtomicResult, FailedOperation

  successful_result = AtomicResult.parse_file("myresult.json")
  failed_result = FailedOperation.parse_file("myfailure.json")
  ```

- You can also run `tcparse` from the command line like this:

  ```sh
  tcparse -h # Get help message for cli

  tcparse ./path/to/tc.out > myoutput.json # Parse TeraChem stdout to json

  tcparse --ignore_xyz ./path/to/tc.out > myoutput.json # Ignore the XYZ file in the TeraChem stdout. Helpful in case the XYZ file is not longer available in the location specified in the file.
  ```

## 🤩 Next Steps

This package will be integrated into [QCEngine](https://github.com/MolSSI/QCEngine) soon. So if you like getting your TeraChem data in this format, you'll be able to drive TeraChem from pure python like this:

```python
from qcelemental.models import Molecule, AtomicInput
from qcengine import compute

molecule = Molecule.from_file("mymolecule.xyz")
atomic_input = AtomicInput(
    molecule=molecule,
    driver="gradient", # "energy" | "gradient" | "hessian"
    model={"method": "b3lyp", "basis": "6-31gs"},
    keywords={"restricted": True, "purify": "no"} # Keywords are optional
    )

# result will be AtomicResult or FailedOperation
result = compute(atomic_input, "terachem")
```

## 💻 Contributing

If there's data you'd like parsed from TeraChem output files, please open an issue in this repo explaining the data items you'd like parsed and include an example output file containing the data, like [this](https://github.com/mtzgroup/tcparse/issues/2).

If you'd like to add a parser yourself see the docstring in `tcparse.parsers` for a primer and see the examples written in the module. Adding a parser for new data is quick and easy :)
