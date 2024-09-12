from qcio import CalcType, ProgramInput

from qcparse.exceptions import EncoderError
from qcparse.models import NativeInput

SUPPORTED_CALCTYPES = {
    CalcType.energy,
    CalcType.gradient,
    CalcType.hessian,
    CalcType.optimization,
    CalcType.transition_state,
}
XYZ_FILENAME = "geometry.xyz"
PADDING = 20  # padding between keyword and value in tc.in


def encode(inp_obj: ProgramInput) -> NativeInput:
    """Translate a ProgramInput into TeraChem inputs files.

    Args:
        inp_obj: The qcio ProgramInput object for a computation.

    Returns:
        NativeInput with .input being a tc.in file and .geometry an xyz file.
    """

    # calctype
    if inp_obj.calctype.value == CalcType.hessian:
        calctype = "frequencies"
    elif inp_obj.calctype.value == CalcType.optimization:
        calctype = "minimize"
    elif inp_obj.calctype.value == CalcType.transition_state:
        calctype = "ts"
    else:
        calctype = inp_obj.calctype.value

    # Collect lines for input file
    inp_lines = []
    inp_lines.append(f"{'run':<{PADDING}} {calctype}")
    # Structure
    inp_lines.append(f"{'coordinates':<{PADDING}} {XYZ_FILENAME}")
    inp_lines.append(f"{'charge':<{PADDING}} {inp_obj.structure.charge}")
    inp_lines.append(f"{'spinmult':<{PADDING}} {inp_obj.structure.multiplicity}")
    # Model
    inp_lines.append(f"{'method':<{PADDING}} {inp_obj.model.method}")
    inp_lines.append(f"{'basis':<{PADDING}} {inp_obj.model.basis}")

    # Keywords
    non_keywords = {
        "charge": ".structure.charge",
        "spinmult": ".structure.multiplicity",
        "run": ".calctype",
        "basis": ".model.basis",
        "method": ".model.method",
    }
    for key, value in inp_obj.keywords.items():
        # Check for keywords that should be passed as structured data
        if key in non_keywords:
            raise EncoderError(
                f"Keyword '{key}' should not be set as a keyword. It "
                f"should be set at '{non_keywords[key]}'",
            )
        # Lowercase booleans
        inp_lines.append(f"{key:<{PADDING}} {str(value).lower()}")
    return NativeInput(
        input_file="\n".join(inp_lines) + "\n",  # End file with newline
        geometry_file=inp_obj.structure.to_xyz(),
        geometry_filename=XYZ_FILENAME,
    )
