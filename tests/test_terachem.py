import pytest
from qcio import CalcType

from qcparse.encoders.terachem import PADDING, XYZ_FILENAME, encode
from qcparse.exceptions import EncoderError, MatchNotFoundError
from qcparse.parsers.terachem import (
    calculation_succeeded,
    parse_calctype,
    parse_energy,
    parse_gradient,
    parse_hessian,
    parse_natoms,
    parse_nmo,
    parse_version_control_details,
    parse_version_string,
)

from .data import gradients, hessians


@pytest.mark.parametrize(
    "filename,energy",
    (
        ("water.energy.out", -76.3861099088),
        ("water.gradient.out", -76.3861099088),
        ("water.frequencies.out", -76.3861099088),
    ),
)
def test_parse_energy(test_data_dir, data_collector, filename, energy):
    with open(test_data_dir / filename) as f:
        tcout = f.read()
    parse_energy(tcout, data_collector)


def test_parse_energy_positive(data_collector):
    energy = 76.3854579982
    parse_energy(f"FINAL ENERGY: {energy} a.u", data_collector)
    assert data_collector.energy == energy


@pytest.mark.parametrize(
    "energy",
    (-7634, 7123),
)
def test_parse_energy_integer(data_collector, energy):
    parse_energy(f"FINAL ENERGY: {energy} a.u", data_collector)
    assert data_collector.energy == energy


def test_parse_energy_raises_exception(data_collector):
    with pytest.raises(MatchNotFoundError):
        parse_energy("No energy here", data_collector)


@pytest.mark.parametrize(
    "filename,calctype",
    (
        ("water.energy.out", CalcType.energy),
        ("water.gradient.out", CalcType.gradient),
        ("water.frequencies.out", CalcType.hessian),
    ),
)
def test_parse_calctype(test_data_dir, filename, calctype):
    with open(test_data_dir / filename) as f:
        string = f.read()
    assert parse_calctype(string) == calctype


def test_parse_calctype_raises_exception():
    with pytest.raises(MatchNotFoundError):
        parse_calctype("No driver here")


def test_parse_version_git(terachem_energy_stdout):
    parsed = parse_version_string(terachem_energy_stdout)
    assert parsed == "v1.9-2022.03-dev [4daa16dd21e78d64be5415f7663c3d7c2785203c]"


def test_parse_version_hg(test_data_dir):
    hg_stdout = (test_data_dir / "hg.out").read_text()
    parsed = parse_version_string(hg_stdout)
    assert parsed == "v1.5K [ccdev]"


def test_calculation_succeeded(terachem_energy_stdout):
    assert calculation_succeeded(terachem_energy_stdout) is True
    assert (
        calculation_succeeded(
            """
        Incorrect purify value
        DIE called at line number 3572 in file terachem/params.cpp
         Job terminated: Thu Mar 23 03:47:12 2023
        """
        )
        is False
    )


@pytest.mark.parametrize(
    "filename,result",
    (
        ("failure.nocuda.out", False),
        ("failure.basis.out", False),
    ),
)
def test_calculation_succeeded_cuda_failure(test_data_dir, filename, result):
    with open(test_data_dir / filename) as f:
        tcout = f.read()
    assert calculation_succeeded(tcout) is result


@pytest.mark.parametrize(
    "filename,gradient",
    (
        (
            "water.gradient.out",
            gradients.water,
        ),
        (
            "caffeine.gradient.out",
            gradients.caffeine,
        ),
        (
            "caffeine.frequencies.out",
            gradients.caffeine_frequencies,
        ),
    ),
)
def test_parse_gradient(test_data_dir, filename, gradient, data_collector):
    with open(test_data_dir / filename) as f:
        tcout = f.read()

    parse_gradient(tcout, data_collector)
    assert data_collector.gradient == gradient


@pytest.mark.parametrize(
    "filename,hessian",
    (
        (
            "water.frequencies.out",
            hessians.water,
        ),
        (
            "caffeine.frequencies.out",
            hessians.caffeine,
        ),
    ),
)
def test_parse_hessian(test_data_dir, filename, hessian, data_collector):
    with open(test_data_dir / filename) as f:
        tcout = f.read()

    parse_hessian(tcout, data_collector)
    assert data_collector.hessian == hessian


@pytest.mark.parametrize(
    "filename,n_atoms",
    (("water.energy.out", 3), ("caffeine.gradient.out", 24)),
)
def test_parse_natoms(test_data_dir, filename, n_atoms, data_collector):
    with open(test_data_dir / filename) as f:
        tcout = f.read()

    parse_natoms(tcout, data_collector)
    assert data_collector.calcinfo_natoms == n_atoms


@pytest.mark.parametrize(
    "filename,nmo",
    (("water.energy.out", 13), ("caffeine.gradient.out", 146)),
)
def test_parse_nmo(test_data_dir, filename, nmo, data_collector):
    with open(test_data_dir / filename) as f:
        tcout = f.read()

    parse_nmo(tcout, data_collector)
    assert data_collector.calcinfo_nmo == nmo


def test_parse_git_commit(terachem_energy_stdout):
    git_commit = parse_version_control_details(terachem_energy_stdout)
    assert (
        git_commit
        == "4daa16dd21e78d64be5415f7663c3d7c2785203c"  # pragma: allowlist secret
    )


def test_write_input_files(prog_inp):
    """Test write_input_files method."""
    prog_inp = prog_inp("energy")

    native_input = encode(prog_inp)
    # Testing that we capture:
    # 1. Driver
    # 2. Structure
    # 3. Model
    # 4. Keywords (test booleans to lower case, ints, sts, floats)

    correct_tcin = (
        f"{'run':<{PADDING}} {prog_inp.calctype}\n"
        f"{'coordinates':<{PADDING}} {XYZ_FILENAME}\n"
        f"{'charge':<{PADDING}} {prog_inp.structure.charge}\n"
        f"{'spinmult':<{PADDING}} {prog_inp.structure.multiplicity}\n"
        f"{'method':<{PADDING}} {prog_inp.model.method}\n"
        f"{'basis':<{PADDING}} {prog_inp.model.basis}\n"
        f"{'purify':<{PADDING}} {prog_inp.keywords['purify']}\n"
        f"{'some-bool':<{PADDING}} "
        f"{str(prog_inp.keywords['some-bool']).lower()}\n"
    )
    assert native_input.input_file == correct_tcin


def test_write_input_files_renames_hessian_to_frequencies(prog_inp):
    """Test write_input_files method for hessian."""
    # Modify input to be a hessian calculation
    prog_inp = prog_inp("hessian")
    native_input = encode(prog_inp)

    assert native_input.input_file == (
        f"{'run':<{PADDING}} frequencies\n"
        f"{'coordinates':<{PADDING}} {XYZ_FILENAME}\n"
        f"{'charge':<{PADDING}} {prog_inp.structure.charge}\n"
        f"{'spinmult':<{PADDING}} {prog_inp.structure.multiplicity}\n"
        f"{'method':<{PADDING}} {prog_inp.model.method}\n"
        f"{'basis':<{PADDING}} {prog_inp.model.basis}\n"
        f"{'purify':<{PADDING}} {prog_inp.keywords['purify']}\n"
        f"{'some-bool':<{PADDING}} "
        f"{str(prog_inp.keywords['some-bool']).lower()}\n"
    )


def test_encode_raises_error_qcio_args_passes_as_keywords(prog_inp):
    """These keywords should not be in the .keywords dict. They belong on structured
    qcio objects instead."""
    qcio_keywords_from_terachem = ["charge", "spinmult", "method", "basis", "run"]
    prog_inp = prog_inp("energy")
    for keyword in qcio_keywords_from_terachem:
        prog_inp.keywords[keyword] = "some value"
        with pytest.raises(EncoderError):
            encode(prog_inp)
