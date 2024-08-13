import pytest
from qcio import ProgramInput, Structure
from qcio.utils import water

from qcparse.encoders.crest import _to_toml_dict, validate_input
from qcparse.exceptions import EncoderError
from qcparse.parsers.crest import (
    parse_conformer_search_dir,
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
