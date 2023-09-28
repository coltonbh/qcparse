import pytest

from qcparse.encoders import terachem
from qcparse.exceptions import EncoderError
from qcparse.main import encode, parse


def test_main_terachem_energy(terachem_energy_stdout):
    computed_props = parse(terachem_energy_stdout, "terachem")
    assert computed_props.energy == -76.3861099088


def test_encode_raises_error_with_invalid_calctype(prog_inp):
    prog_inp = prog_inp("optimization")  # Not currently supported by terachem encoder
    with pytest.raises(EncoderError):
        encode(prog_inp, "terachem")


def test_main_terachem_encoder(prog_inp):
    prog_inp = prog_inp("energy")
    native_input = encode(prog_inp, "terachem")
    correct_tcin = (
        f"{'run':<{terachem.PADDING}} {prog_inp.calctype}\n"
        f"{'coordinates':<{terachem.PADDING}} {terachem.XYZ_FILENAME}\n"
        f"{'charge':<{terachem.PADDING}} {prog_inp.molecule.charge}\n"
        f"{'spinmult':<{terachem.PADDING}} {prog_inp.molecule.multiplicity}\n"
        f"{'method':<{terachem.PADDING}} {prog_inp.model.method}\n"
        f"{'basis':<{terachem.PADDING}} {prog_inp.model.basis}\n"
        f"{'purify':<{terachem.PADDING}} {prog_inp.keywords['purify']}\n"
        f"{'some-bool':<{terachem.PADDING}} "
        f"{str(prog_inp.keywords['some-bool']).lower()}\n"
    )
    assert native_input.input_file == correct_tcin
