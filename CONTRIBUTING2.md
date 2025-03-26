# Parsing Framework Overview

This framework standardizes how output files from quantum chemistry programs are parsed and converted into structured result objects. It separates parsers into two main categories:

1. Standard File Parsers:
   These functions operate on a single file’s contents (e.g., a log file's text). They accept a single input—named contents (which may be a str or bytes)—and return one parsed value. Their output is automatically assigned to a designated key (the target) on the final results object.

2. Composite (Directory) Parsers:
   These functions handle more complex parsing tasks that involve an entire directory of output files. They have a different signature: they receive additional context such as the stdout string, the directory path, and an input object. They return a dictionary mapping keys to parsed values. When no target is specified at registration, the returned dictionary is merged into the final results data.

## Registration of Parsers

All parsers are registered via the @register decorator. The decorator’s parameters are as follows:

- filetype:
  A value (typically from an enum such as FileType) indicating the type of file the parser handles. For example, FileType.stdout for log output or FileType.directory for full-directory processing.

- calctypes (optional):
  A list of calculation types (from the CalcType enum) on which this parser should run. If omitted, the parser applies to all calculation types.

- required:
  A boolean indicating whether this parser is mandatory. If True and the parser fails to parse the expected data, a MatchNotFoundError is raised.

- target (optional for composite parsers):
  For standard file parsers, this key (or nested key as a tuple) indicates where in the final results object the parser’s output should be stored. For composite parsers—those registered with FileType.directory—if no target is provided the parser is expected to return a dictionary, which will be merged into the data collector.

The registry itself enforces that no two parsers for the same program register the same target.

## Example: Standard File Parser

```python
from qcparse import register
from qcparse.models import FileType
from qcio import CalcType
from qcparse.utils import regex_search

@register(filetype=FileType.stdout, target="energy", calctypes=[CalcType.energy])
def parse_energy(contents: str) -> float:
    """
    Parse the final energy from TeraChem stdout.

    Returns:
        The energy as a float.
    """
    regex = r"FINAL ENERGY: (-?\d+(?:\.\d+)?)"
    return float(regex_search(regex, contents).group(1))

```

## Example: Composite (Directory) Parser

In this case, because the parser processes the whole directory output and returns multiple pieces of data, we omit the target. The returned dictionary is merged by the top-level parser.

```python
from qcparse import register
from qcparse.models import FileType
from qcio import CalcType, ProgramInput
from pathlib import Path
import numpy as np

@register(filetype=FileType.directory, calctypes=[CalcType.optimization])
def parse_optimization_dir(stdout: str, directory: Union[str, Path], inp_obj: ProgramInput) -> dict:
    """
    Parse the optimization directory output for TeraChem.

    This composite parser processes additional files (like optim.xyz), extracts the trajectory,
    energy, and other calculation information, and returns a dictionary of results.

    Returns:
        A dictionary with keys such as 'trajectory', 'energy', and 'calcinfo'.
    """
    # Example pseudocode for parsing:
    structures = ...  # Parse structures from directory / "optim.xyz"
    energy = ...      # Extract energy from stdout or file
    trajectory = ...  # Assemble the trajectory (a list of ProgramOutput entries)

    return {
        "trajectory": trajectory,
        "energy": energy,
        # Add additional keys as needed
    }
```

## Top-Level Parsing Function

The parse_new function orchestrates the parsing process:

1.  It collects input files using a unified generator (for example, combining a stdout input with files discovered via iter_files()).

2.  It retrieves the appropriate parsers from the registry based on the program, filetype, and calctype.

3.  It then dispatches:

    - For Standard File Parsers:

      Calls the parser with the file’s contents and assigns the returned value to the specified target.

    - For Composite (Directory) Parsers:

      Calls the parser with additional context (stdout, directory, input object). If the parser returns a dictionary, its key–value pairs are merged into the data collector.

4.  Finally, the assembled data (a dictionary) is passed into the correct result model, using a mapping from calctype to result type.

## Duplicate Target Registration

The registry enforces unique targets per program. This ensures that each parsed value is uniquely associated with a key in the final results. For example, if two parsers attempt to register with the same target for a given program, the registry will raise an error, preventing ambiguity in the final result.

This approach keeps the interface consistent and clear:

- Simple Parsers: Return a single value and specify a target.
- Composite Parsers: Omit the target, return a dictionary, and have their keys merged into the overall results.

This design maintains clarity and minimizes redundant parsing while giving you the flexibility to handle both simple and complex parsing tasks.
