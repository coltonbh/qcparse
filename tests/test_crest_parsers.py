import numpy as np
import pytest
from qcio import ProgramInput

from qcparse.parsers.crest import (
    parse_conformers,
    parse_energy,
    parse_energy_numhess,
    parse_g98_freqs,
    parse_g98_normal_modes,
    parse_gradient,
    parse_numhess1,
    parse_rotamers,
    parse_trajectory,
    parse_version,
)


def test_parse_version(test_data_dir):
    text = (test_data_dir / "crest_stdout.txt").read_text()
    assert parse_version(text) == "3.0.1"


def test_parse_conformers(test_data_dir, prog_inp):
    # Using fake prog_input for water; need .structure.charge and .multiplicity
    data = parse_conformers(
        test_data_dir / "crest_output", None, prog_inp("conformer_search")
    )
    assert len(data["conformers"]) == 3
    # Check conformer energies
    conf_energies = [-107.04437987, -107.04429757, -107.04413699]
    for i, struct in enumerate(data["conformers"]):
        assert data["conformer_energies"][i] == conf_energies[i]
        assert struct.charge == 0
        assert struct.multiplicity == 1


def test_parse_conformers_charge_multiplicity_updates(test_data_dir, prog_inp):
    # Change charge and multiplicity in prog_input
    prog_input = prog_inp("conformer_search")
    prog_input_dict = prog_input.model_dump()
    prog_input_dict["structure"]["charge"] = -2
    prog_input_dict["structure"]["multiplicity"] = 3
    # Using fake prog_input for water; need .structure.charge and .multiplicity
    data = parse_conformers(
        test_data_dir / "crest_output", None, ProgramInput(**prog_input_dict)
    )
    assert len(data["conformers"]) == 3
    # Check conformer energies
    conf_energies = [-107.04437987, -107.04429757, -107.04413699]
    for i, struct in enumerate(data["conformers"]):
        assert data["conformer_energies"][i] == conf_energies[i]
        assert struct.charge == -2
        assert struct.multiplicity == 3


def test_parse_rotamers(test_data_dir, prog_inp):
    # Using fake prog_input for water; need .structure.charge and .multiplicity
    data = parse_rotamers(
        test_data_dir / "crest_output", None, prog_inp("conformer_search")
    )
    assert len(data["rotamers"]) == 2
    # Check conformer energies
    rot_energies = [-107.044379870000, -107.044379830000]
    for i, struct in enumerate(data["rotamers"]):
        assert data["rotamer_energies"][i] == rot_energies[i]
        assert struct.charge == 0
        assert struct.multiplicity == 1


def test_parse_rotamers_charge_multiplicity_updates(test_data_dir, prog_inp):
    # Change charge and multiplicity in prog_input
    prog_input = prog_inp("conformer_search")
    prog_input_dict = prog_input.model_dump()
    prog_input_dict["structure"]["charge"] = 3
    prog_input_dict["structure"]["multiplicity"] = 5
    # Using fake prog_input for water; need .structure.charge and .multiplicity
    data = parse_rotamers(
        test_data_dir / "crest_output", None, ProgramInput(**prog_input_dict)
    )
    assert len(data["rotamers"]) == 2
    # Check conformer energies
    rot_energies = [-107.044379870000, -107.044379830000]
    for i, struct in enumerate(data["rotamers"]):
        assert data["rotamer_energies"][i] == rot_energies[i]
        assert struct.charge == 3
        assert struct.multiplicity == 5


def test_parse_energy(test_data_dir):
    text = (test_data_dir / "crest_output" / "crest.engrad").read_text()
    assert parse_energy(text) == -0.335557824179335


def test_parse_gradient(test_data_dir):
    text = (test_data_dir / "crest_output" / "crest.engrad").read_text()
    assert parse_gradient(text) == [
        [-0.005962071557911, -0.004419818102026, 0.003139227894649],
        [0.003048425211480, 0.001982394235964, -0.001779667371498],
        [0.002913646346432, 0.002437423866062, -0.001359560523152],
    ]


def test_parse_energy_numhess():
    stdout = """
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    Initial singlpoint calculation ...
    -------------------------------------

    Energy =      -110.490788960984773 Eh
    -------------------------------------
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

    Calculating numerical Hessian ... done.
    """
    assert parse_energy_numhess(stdout) == -110.490788960984773


def test_parse_numhess1(test_data_dir):
    contents = (test_data_dir / "crest_output" / "numhess1").read_text()
    # fmt: off
    assert parse_numhess1(contents) == [[0.02040569, -0.00018059, 0.02080099, -0.02081319, 0.01511689, 0.00867078, 0.00037976, -0.01495837, -0.02946283], [-0.00018059, -0.01341723, -0.03209513, 0.01368595, 0.03374600, 0.01874084, -0.01351862, -0.02035995, 0.01336374], [0.02080099, -0.03209513, 0.00327178, 0.00784908, 0.01737681, -0.01812512, -0.02863169, 0.01472059, 0.01485103], [-0.02081319, 0.01368595, 0.00784908, 0.01933555, -0.01625843, -0.00694960, 0.00149263, 0.00258608, -0.00090575], [0.01511689, 0.03374600, 0.01737681, -0.01625843, -0.03409225, -0.01710500, 0.00114214, 0.00035657, -0.00027546], [0.00867078, 0.01874084, -0.01812512, -0.00694960, -0.01710500, 0.01843539, -0.00173455, -0.00164242, -0.00030677], [0.00037976, -0.01351862, -0.02863169, 0.00149263, 0.00114214, -0.00173455, -0.00185964, 0.01238496, 0.03036359], [-0.01495837, -0.02035995, 0.01472059, 0.00258608, 0.00035657, -0.00164242, 0.01238496, 0.02002423, -0.01308397], [-0.02946283, 0.01336374, 0.01485103, -0.00090575, -0.00027546, -0.00030677, 100.03036359, -0.01308397, -12.01454546]]
    # fmt: on


# fmt: off
@pytest.mark.parametrize(
    "filename,expected_freqs",
    (   
        ("g98HF.out", [3533.1374]),
        ("g98.out", [1665.9199, 3662.9967, 3663.6323]),
        ("g98big.out", [-335.2821, 75.3406, 87.4971, 152.4883, 180.0606, 191.074, 219.3003, 246.2166, 278.5267, 280.7177, 359.0875, 382.8016, 449.069, 545.5556, 611.7482, 640.0248, 825.2501, 889.7146, 927.2648, 935.9104, 965.7738, 971.4924, 1066.8035, 1085.231, 1146.0758, 1210.0312, 1325.697, 1354.3222, 1377.8921, 1388.152, 1409.9827, 1415.4545, 1977.5598, 2058.9146, 2600.6465, 2992.0603, 2997.6282, 3014.3359, 3047.3809, 3083.5006, 3090.5364, 3205.2305]),
     )
    
)
# fmt: on
def test_parse_g98_freqs(test_data_dir, filename, expected_freqs):
    """Test the parse_g98_freqs function."""
    contents = (test_data_dir / "crest_output" / filename).read_text()
    parsed_freqs = parse_g98_freqs(contents)
    assert parsed_freqs == expected_freqs


# fmt: off
@pytest.mark.parametrize(
    "filename,expected_nmodes",
    (
        ("g98HF.out",  np.array([[[-0.41573975, 0.0, 0.0], [1.83303434, 0.0, 0.0]]])),   
        ("g98.out", np.array([[[-0.26456166, 0.35904796, -0.18897261], [-0.07558905, -0.90706854, 0.90706854], [1.15273294, -0.54802058, -0.15117809]], [[0.20786987, -0.30235618, 0.17007535], [-1.15273294, 0.3401507, 0.3401507], [0.35904796, 0.8314795, -1.00155485]], [[-0.37794523, -0.09448631, 0.32125344], [1.22832198, -0.37794523, -0.35904796], [0.30235618, 0.77478771, -0.90706854]]])),
        ("g98big.out", "crest_g98big_normal_modes.npy"),
     )
    
)
# fmt: on
def test_parse_g98_normal_modes(test_data_dir, filename, expected_nmodes):
    """Test the parse_g98_normal_modes function."""
    contents = (test_data_dir / "crest_output" / filename).read_text()
    n_modes = parse_g98_normal_modes(contents)
    if isinstance(expected_nmodes, str):
        expected_nmodes = np.load(test_data_dir / expected_nmodes)
    np.testing.assert_array_almost_equal(n_modes,expected_nmodes, decimal=1e-7)


def test_parse_optimization_dir(test_data_dir, prog_inp):
    prog_input = prog_inp("optimization")
    stdout = (test_data_dir / "crest_output" / "optstdout.txt").read_text()
    trajectory = parse_trajectory(
        test_data_dir / "crest_output", stdout, prog_input
    )
    assert len(trajectory) == 13

    # Fills in the final gradient correctly with values from crest.engrad files
    np.testing.assert_array_equal(
        trajectory[-1].results.gradient,
        [
            [-0.005962071557911, -0.004419818102026, 0.003139227894649],
            [0.003048425211480, 0.001982394235964, -0.001779667371498],
            [0.002913646346432, 0.002437423866062, -0.001359560523152],
        ],
    )
