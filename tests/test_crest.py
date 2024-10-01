import numpy as np
import pytest
from qcio import ProgramInput, Structure
from qcio.utils import water

from qcparse.encoders.crest import _to_toml_dict, validate_input
from qcparse.exceptions import EncoderError
from qcparse.parsers.crest import (
    parse_conformer_search_dir,
    parse_energy_grad,
    parse_numhess_dir,
    parse_optimization_dir,
    parse_singlepoint_dir,
    parse_structures,
    parse_version_string,
)


def test_parse_version_string(test_data_dir):
    text = (test_data_dir / "crest_stdout.txt").read_text()
    assert parse_version_string(text) == "3.0.1"


def test_validate_input(prog_inp):
    inp_obj = prog_inp("conformer_search")
    validate_input(inp_obj)

    with pytest.raises(EncoderError):
        inp_obj.keywords["charge"] = -1
        validate_input(inp_obj)

    with pytest.raises(EncoderError):
        inp_obj.keywords["uhf"] = 0
        validate_input(inp_obj)

    with pytest.raises(EncoderError):
        inp_obj.keywords["runtype"] = "imtd-gc"
        validate_input(inp_obj)


def test_toml_dict():
    """Test converting a ProgramInput object to a TOML dictionary for CREST."""

    weird_water = water.model_copy(update={"charge": -1, "multiplicity": 2})
    inp_obj = ProgramInput(
        structure=weird_water,
        calctype="conformer_search",
        model={"method": "gfn2"},
        keywords={"calculation": {"level": [{"alpb": "acetonitrile"}]}},
    )

    toml_dict = _to_toml_dict(inp_obj, "struct.xyz")

    assert toml_dict["input"] == "struct.xyz"
    assert toml_dict["runtype"] == "imtd-gc"
    assert toml_dict.get("threads") is not None  # added implicitly if not set

    # Adds values correctly to existing "calculation" key
    assert toml_dict["calculation"]["level"][0]["method"] == "gfn2"
    assert toml_dict["calculation"]["level"][0]["charge"] == -1
    assert toml_dict["calculation"]["level"][0]["uhf"] == 1
    assert toml_dict["calculation"]["level"][0]["alpb"] == "acetonitrile"

    # Respects explicitly set threads and handles no "calculation" key
    inp_obj = ProgramInput(
        structure=weird_water,
        calctype="conformer_search",
        model={"method": "gfn2"},
        keywords={"threads": 2},
    )

    toml_dict = _to_toml_dict(inp_obj, "struct.xyz")
    assert toml_dict["threads"] == 2
    assert toml_dict["calculation"]["level"][0]["method"] == "gfn2"
    assert toml_dict["calculation"]["level"][0]["charge"] == -1
    assert toml_dict["calculation"]["level"][0]["uhf"] == 1


def test_parse_structures(test_data_dir):
    structs = parse_structures(test_data_dir / "crest_output" / "crest_conformers.xyz")
    assert len(structs) == 3
    energies = [-107.04437987, -107.04429757, -107.04413699]
    for i, struct in enumerate(structs):
        assert float(struct.extras[Structure._xyz_comment_key][0]) == energies[i]
        assert struct.formula == "C17H7F12N2O"


def test_parse_structure_no_file():
    assert parse_structures("no_file.xyz") == []


def test_parse_conformer_search_dir(test_data_dir):
    csr = parse_conformer_search_dir(test_data_dir / "crest_output")
    assert len(csr.conformers) == 3
    assert len(csr.rotamers) == 2
    # Check conformer energies
    conf_energies = [-107.04437987, -107.04429757, -107.04413699]
    for i, struct in enumerate(csr.conformers):
        assert csr.conformer_energies[i] == conf_energies[i]
        assert struct.charge == 0
        assert struct.multiplicity == 1
    # Check rotamer energies
    rot_energies = [-107.044379870000, -107.044379830000]
    for i, struct in enumerate(csr.rotamers):
        assert csr.rotamer_energies[i] == rot_energies[i]
        assert struct.charge == 0
        assert struct.multiplicity == 1


def test_parse_conformer_search_charge_multiplicity(test_data_dir):
    csr = parse_conformer_search_dir(
        test_data_dir / "crest_output", charge=-2, multiplicity=3
    )
    for struct_type in ["conformers", "rotamers"]:
        for struct in getattr(csr, struct_type):
            assert struct.charge == -2
            assert struct.multiplicity == 3


def test_parse_energy_grad(test_data_dir):
    text = (test_data_dir / "crest_output" / "crest.engrad").read_text()
    spr = parse_energy_grad(text)
    assert spr.energy == -0.335557824179335
    np.testing.assert_array_equal(
        spr.gradient,
        [
            [-0.005962071557911, -0.004419818102026, 0.003139227894649],
            [0.003048425211480, 0.001982394235964, -0.001779667371498],
            [0.002913646346432, 0.002437423866062, -0.001359560523152],
        ],
    )


def test_parse_singlepoint_dir(test_data_dir):
    spr = parse_singlepoint_dir(test_data_dir / "crest_output")
    assert spr.energy == -0.335557824179335
    np.testing.assert_array_equal(
        spr.gradient,
        [
            [-0.005962071557911, -0.004419818102026, 0.003139227894649],
            [0.003048425211480, 0.001982394235964, -0.001779667371498],
            [0.002913646346432, 0.002437423866062, -0.001359560523152],
        ],
    )


def test_parse_optimization_dir(test_data_dir, prog_inp):
    prog_input = prog_inp("optimization")
    stdout = (test_data_dir / "crest_output" / "optstdout.txt").read_text()
    opt_res = parse_optimization_dir(
        test_data_dir / "crest_output", inp_obj=prog_input, stdout=stdout
    )
    assert len(opt_res.trajectory) == 13

    # Fills in the final gradient correctly with values from crest.engrad files
    np.testing.assert_array_equal(
        opt_res.trajectory[-1].results.gradient,
        [
            [-0.005962071557911, -0.004419818102026, 0.003139227894649],
            [0.003048425211480, 0.001982394235964, -0.001779667371498],
            [0.002913646346432, 0.002437423866062, -0.001359560523152],
        ],
    )


def test_parse_numhess_dir(test_data_dir):
    stdout = """
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    Initial singlpoint calculation ...
    -------------------------------------

    Energy =      -110.490788960984773 Eh
    -------------------------------------
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

    Calculating numerical Hessian ... done.
    """
    spr = parse_numhess_dir(test_data_dir / "crest_output", stdout=stdout)
    assert spr.energy == -110.490788960984773
    np.testing.assert_array_equal(
        spr.hessian,
        [
            [
                0.02040569,
                -0.00018059,
                0.02080099,
                -0.02081319,
                0.01511689,
                0.00867078,
                0.00037976,
                -0.01495837,
                -0.02946283,
            ],
            [
                -0.00018059,
                -0.01341723,
                -0.03209513,
                0.01368595,
                0.03374600,
                0.01874084,
                -0.01351862,
                -0.02035995,
                0.01336374,
            ],
            [
                0.02080099,
                -0.03209513,
                0.00327178,
                0.00784908,
                0.01737681,
                -0.01812512,
                -0.02863169,
                0.01472059,
                0.01485103,
            ],
            [
                -0.02081319,
                0.01368595,
                0.00784908,
                0.01933555,
                -0.01625843,
                -0.00694960,
                0.00149263,
                0.00258608,
                -0.00090575,
            ],
            [
                0.01511689,
                0.03374600,
                0.01737681,
                -0.01625843,
                -0.03409225,
                -0.01710500,
                0.00114214,
                0.00035657,
                -0.00027546,
            ],
            [
                0.00867078,
                0.01874084,
                -0.01812512,
                -0.00694960,
                -0.01710500,
                0.01843539,
                -0.00173455,
                -0.00164242,
                -0.00030677,
            ],
            [
                0.00037976,
                -0.01351862,
                -0.02863169,
                0.00149263,
                0.00114214,
                -0.00173455,
                -0.00185964,
                0.01238496,
                0.03036359,
            ],
            [
                -0.01495837,
                -0.02035995,
                0.01472059,
                0.00258608,
                0.00035657,
                -0.00164242,
                0.01238496,
                0.02002423,
                -0.01308397,
            ],
            [
                -0.02946283,
                0.01336374,
                0.01485103,
                -0.00090575,
                -0.00027546,
                -0.00030677,
                0.03036359,
                -0.01308397,
                -0.01454546,
            ],
        ],
    )
