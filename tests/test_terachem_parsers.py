import numpy as np
import pytest
from qcio import CalcType

from qcparse.exceptions import MatchNotFoundError
from qcparse.main import decode
from qcparse.parsers.terachem import (
    calculation_succeeded,
    parse_calctype,
    parse_energy,
    parse_gradient,
    parse_gradients,
    parse_hessian,
    parse_natoms,
    parse_nmo,
    parse_trajectory,
    parse_version,
    parse_version_control_details,
    parse_excited_states,
)

from .data import gradients, hessians, excited_states


@pytest.mark.parametrize(
    "filename,expected_energy",
    (
        ("water.energy.out", -76.3861099088),
        ("water.gradient.out", -76.3861099088),
        ("water.frequencies.out", -76.3861099088),
        ("caffeine.gradient.out", -680.1453428559),
    ),
)
def test_parse_energy(test_data_dir, filename, expected_energy):
    with open(test_data_dir / filename) as f:
        tcout = f.read()
    result = parse_energy(tcout)
    assert result == expected_energy


def test_parse_energy_positive():
    energy = 76.3854579982
    result = parse_energy(f"FINAL ENERGY: {energy} a.u")
    assert result == energy


@pytest.mark.parametrize(
    "energy",
    (-7634, 7123),
)
def test_parse_energy_integer(energy):
    result = parse_energy(f"FINAL ENERGY: {energy} a.u")
    assert result == energy


def test_parse_energy_raises_exception():
    with pytest.raises(MatchNotFoundError):
        parse_energy("No energy here")


def test_top_level_energy(test_data_dir):
    with open(test_data_dir / "water.energy.out") as f:
        stdout_str = f.read()
    expected_energy = -76.3861099088
    results = decode(program="terachem", calctype=CalcType.energy, stdout=stdout_str)

    # Check that the energy value is present and correct
    assert hasattr(results, "energy"), "Results should have an 'energy' attribute."
    assert (
        results.energy == expected_energy
    ), f"Expected energy {expected_energy}, got {results.energy}"


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
    parsed = parse_version(terachem_energy_stdout)
    assert parsed == "v1.9-2022.03-dev [4daa16dd21e78d64be5415f7663c3d7c2785203c]"


def test_parse_version_hg(test_data_dir):
    hg_stdout = (test_data_dir / "hg.out").read_text()
    parsed = parse_version(hg_stdout)
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
    "filename,expected_gradient",
    (
        ("water.gradient.out", gradients.water),
        ("caffeine.gradient.out", gradients.caffeine),
        ("caffeine.frequencies.out", gradients.caffeine_frequencies),
    ),
)
def test_parse_gradient(test_data_dir, filename, expected_gradient):
    with open(test_data_dir / filename) as f:
        tcout = f.read()
    result = parse_gradient(tcout)
    assert result == expected_gradient


def test_top_level_gradient(test_data_dir):
    with open(test_data_dir / "water.gradient.out") as f:
        stdout_str = f.read()
    results = decode(program="terachem", calctype=CalcType.gradient, stdout=stdout_str)

    # Check that the energy value is present and correct
    assert hasattr(results, "gradient"), "Results should have an 'gradient' attribute."
    np.testing.assert_allclose(
        results.gradient,
        gradients.water,
        err_msg=f"Expected gradient {gradients.water}, got {results.gradient}",
    )


@pytest.mark.parametrize(
    "filename,expected_hessian",
    (
        ("water.frequencies.out", hessians.water),
        ("caffeine.frequencies.out", hessians.caffeine),
    ),
)
def test_parse_hessian(test_data_dir, filename, expected_hessian):
    with open(test_data_dir / filename) as f:
        tcout = f.read()

    result = parse_hessian(tcout)
    assert result == expected_hessian


def test_top_level_hessian(test_data_dir):
    with open(test_data_dir / "water.frequencies.out") as f:
        stdout_str = f.read()
    results = decode(program="terachem", calctype=CalcType.hessian, stdout=stdout_str)

    # Check that the energy value is present and correct
    assert hasattr(results, "hessian"), "Results should have an 'hessian' attribute."
    np.testing.assert_allclose(
        results.hessian,
        hessians.water,
        err_msg=f"Expected hessian {hessians.water}, got {results.hessian}",
    )


@pytest.mark.parametrize(
    "filename,n_atoms",
    (("water.energy.out", 3), ("caffeine.gradient.out", 24)),
)
def test_parse_natoms(test_data_dir, filename, n_atoms):
    with open(test_data_dir / filename) as f:
        tcout = f.read()

    assert parse_natoms(tcout) == n_atoms


@pytest.mark.parametrize(
    "filename,nmo",
    (("water.energy.out", 13), ("caffeine.gradient.out", 146)),
)
def test_parse_nmo(test_data_dir, filename, nmo):
    with open(test_data_dir / filename) as f:
        tcout = f.read()

    assert parse_nmo(tcout) == nmo


def test_parse_git_commit(terachem_energy_stdout):
    git_commit = parse_version_control_details(terachem_energy_stdout)
    assert (
        git_commit
        == "4daa16dd21e78d64be5415f7663c3d7c2785203c"  # pragma: allowlist secret
    )


def test_parse_gradients(test_data_dir):
    stdout_opt = (test_data_dir / "terachem_opt" / "tc.out").read_text()

    parsed_gradients = parse_gradients(stdout_opt)
    assert parsed_gradients == gradients.water_opt


def test_parse_trajectory(test_data_dir, prog_inp):
    opt_inp = prog_inp("optimization")
    stdout = (test_data_dir / "terachem_opt" / "tc.out").read_text()
    trajectory = parse_trajectory(
        test_data_dir / "terachem_opt", stdout, input_data=opt_inp
    )
    for prog_output in trajectory:
        assert prog_output.input_data.calctype == CalcType.gradient
        assert prog_output.input_data.model == opt_inp.model
        assert prog_output.input_data.keywords == opt_inp.keywords
        assert prog_output.success is True
        assert prog_output.provenance.program == "terachem"
        assert (
            prog_output.provenance.program_version
            == "v1.9-2023.09-dev [2407d3d72955905cdd9c0dproae51e9322b8c05fd4c]"
        )
        assert prog_output.provenance.scratch_dir == test_data_dir


@pytest.mark.parametrize(
    "filename,excited_states",
    (
        (
            "water.tddft.out",
            excited_states.water,
        ),
        (
            "caffeine.tddft.out",
            excited_states.caffeine,
        ),
    ),
)
def test_parse_excited_states(test_data_dir, filename, excited_states):
    """
    Tests the parse_excited_states function to ensure that it correctly parses
    excited states from TDDFT output files.
    """
    with open(test_data_dir / filename) as f:
        tcout = f.read()

    parsed_excited_states = parse_excited_states(tcout)
    assert parsed_excited_states == excited_states


def test_parse_excited_states_raises_exception_no_excited_states(test_data_dir):
    """
    Tests the parse_excited_states function to ensure that it correctly raises
    an exception when no excited states are found in the output file.
    """
    with open(test_data_dir / "water.energy.out") as f:
        tcout = f.read()

    with pytest.raises(MatchNotFoundError):
        parse_excited_states(tcout)
