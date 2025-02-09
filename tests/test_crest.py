import numpy as np
import pytest
from qcio import ProgramInput, Structure
from qcio.utils import water

from qcparse.encoders.crest import _to_toml_dict, validate_input
from qcparse.exceptions import EncoderError
from qcparse.parsers.crest import (
    parse_conformer_search_dir,
    parse_energy_grad,
    parse_g98_text,
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
    # fmt: off
    np.testing.assert_array_equal(spr.hessian, [[0.02040569, -0.00018059, 0.02080099, -0.02081319, 0.01511689, 0.00867078, 0.00037976, -0.01495837, -0.02946283], [-0.00018059, -0.01341723, -0.03209513, 0.01368595, 0.03374600, 0.01874084, -0.01351862, -0.02035995, 0.01336374], [0.02080099, -0.03209513, 0.00327178, 0.00784908, 0.01737681, -0.01812512, -0.02863169, 0.01472059, 0.01485103], [-0.02081319, 0.01368595, 0.00784908, 0.01933555, -0.01625843, -0.00694960, 0.00149263, 0.00258608, -0.00090575], [0.01511689, 0.03374600, 0.01737681, -0.01625843, -0.03409225, -0.01710500, 0.00114214, 0.00035657, -0.00027546], [0.00867078, 0.01874084, -0.01812512, -0.00694960, -0.01710500, 0.01843539, -0.00173455, -0.00164242, -0.00030677], [0.00037976, -0.01351862, -0.02863169, 0.00149263, 0.00114214, -0.00173455, -0.00185964, 0.01238496, 0.03036359], [-0.01495837, -0.02035995, 0.01472059, 0.00258608, 0.00035657, -0.00164242, 0.01238496, 0.02002423, -0.01308397], [-0.02946283, 0.01336374, 0.01485103, -0.00090575, -0.00027546, -0.00030677, 0.03036359, -0.01308397, -0.01454546]])
    # fmt: on


def test_parse_g98_text(test_data_dir):
    text = (test_data_dir / "crest_output" / "g98.out").read_text()
    spr_dict = parse_g98_text(text)
    assert spr_dict["freqs_wavenumber"] == [1665.9199, 3662.9967, 3663.6323]
    # fmt: off
    np.testing.assert_array_almost_equal(spr_dict["normal_modes_cartesian"], np.array([[[-0.26456166, 0.35904796, -0.18897261], [-0.07558905, -0.90706854, 0.90706854], [1.15273294, -0.54802058, -0.15117809]], [[0.20786987, -0.30235618, 0.17007535], [-1.15273294, 0.3401507, 0.3401507], [0.35904796, 0.8314795, -1.00155485]], [[-0.37794523, -0.09448631, 0.32125344], [1.22832198, -0.37794523, -0.35904796], [0.30235618, 0.77478771, -0.90706854]]]), decimal=1e-7)
    
    # Non multiple of 3 normal modes
    text = (test_data_dir / "crest_output" / "g98HF.out").read_text()
    spr_dict = parse_g98_text(text)
    assert spr_dict["freqs_wavenumber"] == [3533.1374]
    np.testing.assert_array_almost_equal(spr_dict["normal_modes_cartesian"], np.array([[[-0.41573975, 0.0, 0.0], [1.83303434, 0.0, 0.0]]]), decimal=1e-7)

    # Non multiple of 3 normal modes
    text = (test_data_dir / "crest_output" / "g98big.out").read_text()
    spr_dict = parse_g98_text(text)
    assert spr_dict["freqs_wavenumber"] == [-335.2821, 75.3406, 87.4971, 152.4883, 180.0606, 191.074, 219.3003, 246.2166, 278.5267, 280.7177, 359.0875, 382.8016, 449.069, 545.5556, 611.7482, 640.0248, 825.2501, 889.7146, 927.2648, 935.9104, 965.7738, 971.4924, 1066.8035, 1085.231, 1146.0758, 1210.0312, 1325.697, 1354.3222, 1377.8921, 1388.152, 1409.9827, 1415.4545, 1977.5598, 2058.9146, 2600.6465, 2992.0603, 2997.6282, 3014.3359, 3047.3809, 3083.5006, 3090.5364, 3205.2305]
    # np.testing.assert_array_almost_equal(spr_dict["normal_modes_cartesian"], np.array([[[-0.41573975, 0.0, 0.0], [1.83303434, 0.0, 0.0]]]), decimal=1e-7)
    parsed_g98big = np.load(test_data_dir / "crest_g98big_normal_modes.npy")
    np.testing.assert_array_equal(spr_dict["normal_modes_cartesian"],parsed_g98big) 
    # fmt: on
