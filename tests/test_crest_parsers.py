from qcio import ProgramInput

from qcparse.parsers.crest import (
    parse_conformers,
    # parse_conformer_search_dir,
    parse_energy,
    parse_gradient,
    parse_rotamers,
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


# def test_parse_singlepoint_dir(test_data_dir):
#     spr = parse_singlepoint_dir(test_data_dir / "crest_output")
#     assert spr.energy == -0.335557824179335
#     np.testing.assert_array_equal(
#         spr.gradient,
#         [
#             [-0.005962071557911, -0.004419818102026, 0.003139227894649],
#             [0.003048425211480, 0.001982394235964, -0.001779667371498],
#             [0.002913646346432, 0.002437423866062, -0.001359560523152],
#         ],
#     )


# def test_parse_optimization_dir(test_data_dir, prog_inp):
#     prog_input = prog_inp("optimization")
#     stdout = (test_data_dir / "crest_output" / "optstdout.txt").read_text()
#     opt_res = parse_optimization_dir(
#         test_data_dir / "crest_output", inp_obj=prog_input, stdout=stdout
#     )
#     assert len(opt_res.trajectory) == 13

#     # Fills in the final gradient correctly with values from crest.engrad files
#     np.testing.assert_array_equal(
#         opt_res.trajectory[-1].results.gradient,
#         [
#             [-0.005962071557911, -0.004419818102026, 0.003139227894649],
#             [0.003048425211480, 0.001982394235964, -0.001779667371498],
#             [0.002913646346432, 0.002437423866062, -0.001359560523152],
#         ],
#     )


# def test_parse_numhess_dir(test_data_dir):
#     stdout = """
#     ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#     Initial singlpoint calculation ...
#     -------------------------------------

#     Energy =      -110.490788960984773 Eh
#     -------------------------------------
#     ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

#     Calculating numerical Hessian ... done.
#     """
#     spr = parse_numhess_dir(test_data_dir / "crest_output", stdout=stdout)
#     assert spr.energy == -110.490788960984773
#     # fmt: off
#     np.testing.assert_array_equal(spr.hessian, [[0.02040569, -0.00018059, 0.02080099, -0.02081319, 0.01511689, 0.00867078, 0.00037976, -0.01495837, -0.02946283], [-0.00018059, -0.01341723, -0.03209513, 0.01368595, 0.03374600, 0.01874084, -0.01351862, -0.02035995, 0.01336374], [0.02080099, -0.03209513, 0.00327178, 0.00784908, 0.01737681, -0.01812512, -0.02863169, 0.01472059, 0.01485103], [-0.02081319, 0.01368595, 0.00784908, 0.01933555, -0.01625843, -0.00694960, 0.00149263, 0.00258608, -0.00090575], [0.01511689, 0.03374600, 0.01737681, -0.01625843, -0.03409225, -0.01710500, 0.00114214, 0.00035657, -0.00027546], [0.00867078, 0.01874084, -0.01812512, -0.00694960, -0.01710500, 0.01843539, -0.00173455, -0.00164242, -0.00030677], [0.00037976, -0.01351862, -0.02863169, 0.00149263, 0.00114214, -0.00173455, -0.00185964, 0.01238496, 0.03036359], [-0.01495837, -0.02035995, 0.01472059, 0.00258608, 0.00035657, -0.00164242, 0.01238496, 0.02002423, -0.01308397], [-0.02946283, 0.01336374, 0.01485103, -0.00090575, -0.00027546, -0.00030677, 0.03036359, -0.01308397, -0.01454546]])
#     # fmt: on


# def test_parse_g98_text(test_data_dir):
#     text = (test_data_dir / "crest_output" / "g98.out").read_text()
#     spr_dict = parse_g98_text(text)
#     assert spr_dict["freqs_wavenumber"] == [1665.9199, 3662.9967, 3663.6323]
#     # fmt: off
#     np.testing.assert_array_almost_equal(spr_dict["normal_modes_cartesian"], np.array([[[-0.26456166, 0.35904796, -0.18897261], [-0.07558905, -0.90706854, 0.90706854], [1.15273294, -0.54802058, -0.15117809]], [[0.20786987, -0.30235618, 0.17007535], [-1.15273294, 0.3401507, 0.3401507], [0.35904796, 0.8314795, -1.00155485]], [[-0.37794523, -0.09448631, 0.32125344], [1.22832198, -0.37794523, -0.35904796], [0.30235618, 0.77478771, -0.90706854]]]), decimal=1e-7)

#     # Non multiple of 3 normal modes
#     text = (test_data_dir / "crest_output" / "g98HF.out").read_text()
#     spr_dict = parse_g98_text(text)
#     assert spr_dict["freqs_wavenumber"] == [3533.1374]
#     np.testing.assert_array_almost_equal(spr_dict["normal_modes_cartesian"], np.array([[[-0.41573975, 0.0, 0.0], [1.83303434, 0.0, 0.0]]]), decimal=1e-7)

#     # Non multiple of 3 normal modes
#     text = (test_data_dir / "crest_output" / "g98big.out").read_text()
#     spr_dict = parse_g98_text(text)
#     assert spr_dict["freqs_wavenumber"] == [-335.2821, 75.3406, 87.4971, 152.4883, 180.0606, 191.074, 219.3003, 246.2166, 278.5267, 280.7177, 359.0875, 382.8016, 449.069, 545.5556, 611.7482, 640.0248, 825.2501, 889.7146, 927.2648, 935.9104, 965.7738, 971.4924, 1066.8035, 1085.231, 1146.0758, 1210.0312, 1325.697, 1354.3222, 1377.8921, 1388.152, 1409.9827, 1415.4545, 1977.5598, 2058.9146, 2600.6465, 2992.0603, 2997.6282, 3014.3359, 3047.3809, 3083.5006, 3090.5364, 3205.2305]
#     # np.testing.assert_array_almost_equal(spr_dict["normal_modes_cartesian"], np.array([[[-0.41573975, 0.0, 0.0], [1.83303434, 0.0, 0.0]]]), decimal=1e-7)
#     parsed_g98big = np.load(test_data_dir / "crest_g98big_normal_modes.npy")
#     np.testing.assert_array_equal(spr_dict["normal_modes_cartesian"],parsed_g98big)
#     # fmt: on
