import numpy as np
import pytest
from qcio import CalcType

from qcparse.codec import decode
from qcparse.exceptions import MatchNotFoundError
from qcparse.parsers.terachem import (
    calculation_succeeded,
    parse_calctype,
    parse_energy,
    parse_excited_states,
    parse_gradient,
    parse_gradients,
    parse_hessian,
    parse_natoms,
    parse_nmo,
    parse_trajectory,
    parse_version,
    parse_version_control_details,
)

from .data.terachem.answers import excited_states, gradients, hessians


@pytest.mark.parametrize(
    "filename,expected_energy",
    (
        ("water.energy.out", -76.3861099088),
        ("water.gradient.out", -76.3861099088),
        ("water.frequencies.out", -76.3861099088),
        ("caffeine.gradient.out", -680.1453428559),
    ),
)
def test_parse_energy(terachem_file, filename, expected_energy):
    tcout = terachem_file(filename)
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


def test_top_level_energy(terachem_file):
    stdout = terachem_file("water.energy.out")
    expected_energy = -76.3861099088
    results = decode("terachem", CalcType.energy, stdout=stdout)

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
def test_parse_calctype(terachem_file, filename, calctype):
    contents = terachem_file(filename)
    assert parse_calctype(contents) == calctype


def test_parse_calctype_raises_exception():
    with pytest.raises(MatchNotFoundError):
        parse_calctype("No driver here")


def test_parse_version_git(terachem_file):
    contents = terachem_file("water.energy.out")
    assert (
        parse_version(contents)
        == "v1.9-2022.03-dev [4daa16dd21e78d64be5415f7663c3d7c2785203c]"
    )


def test_parse_version_hg(terachem_file):
    contents = terachem_file("hg.out")
    parsed = parse_version(contents)
    assert parsed == "v1.5K [ccdev]"


def test_calculation_succeeded(terachem_file):
    contents = terachem_file("water.energy.out")
    assert calculation_succeeded(contents) is True
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
def test_calculation_succeeded_cuda_failure(terachem_file, filename, result):
    contents = terachem_file(filename)
    assert calculation_succeeded(contents) is result


@pytest.mark.parametrize(
    "filename,expected_gradient",
    (
        ("water.gradient.out", gradients.water),
        ("caffeine.gradient.out", gradients.caffeine),
        ("caffeine.frequencies.out", gradients.caffeine_frequencies),
    ),
)
def test_parse_gradient(terachem_file, filename, expected_gradient):
    contents = terachem_file(filename)
    result = parse_gradient(contents)
    assert result == expected_gradient


def test_top_level_gradient(terachem_file):
    contents = terachem_file("water.gradient.out")
    results = decode(program="terachem", calctype=CalcType.gradient, stdout=contents)

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
def test_parse_hessian(terachem_file, filename, expected_hessian):
    contents = terachem_file(filename)
    result = parse_hessian(contents)
    assert result == expected_hessian


def test_top_level_hessian(terachem_file):
    contents = terachem_file("water.frequencies.out")
    results = decode(program="terachem", calctype=CalcType.hessian, stdout=contents)

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
def test_parse_natoms(terachem_file, filename, n_atoms):
    contents = terachem_file(filename)
    assert parse_natoms(contents) == n_atoms


@pytest.mark.parametrize(
    "filename,nmo",
    (("water.energy.out", 13), ("caffeine.gradient.out", 146)),
)
def test_parse_nmo(terachem_file, filename, nmo):
    tcout = terachem_file(filename)
    assert parse_nmo(tcout) == nmo


def test_parse_git_commit(terachem_file):
    contents = terachem_file("water.energy.out")
    assert (
        parse_version_control_details(contents)
        == "4daa16dd21e78d64be5415f7663c3d7c2785203c"  # pragma: allowlist secret
    )


def test_parse_gradients(terachem_file):
    contents = terachem_file("water.opt.out")
    parsed_gradients = parse_gradients(contents)
    assert parsed_gradients == gradients.water_opt


def test_parse_trajectory(terachem_file, test_data_dir, prog_inp):
    # Setup the test data
    opt_inp = prog_inp("optimization")
    stdout = terachem_file("water.opt.out")
    directory = test_data_dir / "terachem"

    trajectory = parse_trajectory(directory, stdout, input_data=opt_inp)
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
def test_parse_excited_states(terachem_file, filename, excited_states):
    """
    Tests the parse_excited_states function to ensure that it correctly parses
    excited states from TDDFT output files.
    """
    contents = terachem_file(filename)
    parsed_excited_states = parse_excited_states(contents)
    assert parsed_excited_states == excited_states


def test_parse_excited_states_raises_exception_no_excited_states(terachem_file):
    """
    Tests the parse_excited_states function to ensure that it correctly raises
    an exception when no excited states are found in the output file.
    """
    contents = terachem_file("water.energy.out")

    with pytest.raises(MatchNotFoundError):
        parse_excited_states(contents)
