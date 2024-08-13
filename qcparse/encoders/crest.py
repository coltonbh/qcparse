import copy
import os
from typing import Any, Dict

import tomli_w
from qcio import CalcType, ProgramInput

from qcparse.exceptions import EncoderError
from qcparse.models import NativeInput

SUPPORTED_CALCTYPES = {CalcType.conformer_search}


def encode(inp_obj: ProgramInput) -> NativeInput:
    """Translate a ProgramInput into CREST inputs files.

    Args:
        inp_obj: The qcio ProgramInput object for a computation.

    Returns:
        NativeInput with .input_files being a crest.toml file and .geometry_file the
            Structure's xyz file.
    """
    validate_input(inp_obj)
    struct_filename = "structure.xyz"

    return NativeInput(
        input_file=tomli_w.dumps(_to_toml_dict(inp_obj, struct_filename)),
        geometry_file=inp_obj.structure.to_xyz(),
        geometry_filename=struct_filename,
    )


def validate_input(inp_obj: ProgramInput):
    """Validate the input for CREST.

    Args:
        inp_obj: The qcio ProgramInput object for a computation.

    Raises:
        EncoderError: If the input is invalid.
    """
    # These values come from other parts of the ProgramInput and should not be set
    # in the keywords.
    non_allowed_keywords = ["charge", "uhf", "runtype"]
    for keyword in non_allowed_keywords:
        if keyword in inp_obj.keywords:
            raise EncoderError(
                f"{keyword} should not be set in keywords for CREST. It is already set "
                "on the Structure or ProgramInput elsewhere.",
            )


def _to_toml_dict(inp_obj: ProgramInput, struct_filename: str) -> Dict[str, Any]:
    """Convert a ProgramInput object to a dictionary in the CREST format of TOML.

    This function makes it easier to test for the correct TOML structure.
    """
    # Start with existing keywords
    toml_dict = copy.deepcopy(inp_obj.keywords)

    # Top level keywords
    # Logical cores was 10% faster than physical cores, so not using psutil
    toml_dict.setdefault("threads", os.cpu_count())
    toml_dict["input"] = struct_filename

    # TODO: May need to deal with non-covalent mode at some point
    toml_dict["runtype"] = "imtd-gc"

    # Calculation level keywords
    calculation = toml_dict.pop("calculation", {})
    calculation_level = calculation.pop("level", [])
    if len(calculation_level) == 0:
        calculation_level.append({})
    for level_dict in calculation_level:
        level_dict["method"] = inp_obj.model.method
        level_dict["charge"] = inp_obj.structure.charge
        level_dict["uhf"] = inp_obj.structure.multiplicity - 1

    calculation["level"] = calculation_level
    toml_dict["calculation"] = calculation

    return toml_dict
