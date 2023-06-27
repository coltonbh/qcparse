from pathlib import Path

import pytest

from qcparse.exceptions import MatchNotFoundError
from qcparse.parsers.terachem import (
    CalcType,
    calculation_succeeded,
    parse_calc_type,
    parse_basis,
    parse_energy,
    parse_failure_text,
    parse_gradient,
    parse_hessian,
    parse_method,
    parse_natoms,
    parse_nmo,
    parse_version,
    parse_molecule_spin_multiplicity,
    parse_molecule_charge,
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
    assert data_collector.computed.energy == energy


@pytest.mark.parametrize(
    "energy",
    (-7634, 7123),
)
def test_parse_energy_integer(data_collector, energy):
    parse_energy(f"FINAL ENERGY: {energy} a.u", data_collector)
    assert data_collector.computed.energy == energy


def test_parse_energy_raises_exception(data_collector):
    with pytest.raises(MatchNotFoundError):
        parse_energy("No energy here", data_collector)


@pytest.mark.parametrize(
    "filename,calc_type",
    (
        ("water.energy.out", CalcType.energy),
        ("water.gradient.out", CalcType.gradient),
        ("water.frequencies.out", CalcType.hessian),
    ),
)
def test_parse_calc_type(test_data_dir, filename, calc_type):
    with open(test_data_dir / filename) as f:
        string = f.read()
    assert parse_calc_type(string) == calc_type


def test_parse_calc_type_raises_exception():
    with pytest.raises(MatchNotFoundError):
        parse_calc_type("No driver here")


# @pytest.mark.parametrize(
#     "string,path",
#     (
#         ("XYZ coordinates water.xyz", Path("water.xyz")),
#         ("XYZ coordinates water", Path("water")),
#         ("XYZ coordinates /scratch/water.xyz", Path("/scratch/water.xyz")),
#         ("XYZ coordinates ../water.xyz", Path("../water.xyz")),
#     ),
# )
@pytest.mark.parametrize(
    "filename,method",
    (
        ("water.energy.out", "B3LYP"),
        ("water.gradient.out", "B3LYP"),
        ("water.frequencies.out", "B3LYP"),
    ),
)
def test_parse_method(test_data_dir, filename, method, data_collector):
    with open(test_data_dir / filename) as f:
        tcout = f.read()
    parse_method(tcout, data_collector)
    assert data_collector.input_data.program_args.model.method == method


def test_parse_basis(energy_output, data_collector):
    parse_basis(energy_output, data_collector)
    assert data_collector.input_data.program_args.model.basis == "6-31g"


def test_parse_version(energy_output, data_collector):
    parse_version(energy_output, data_collector)
    assert data_collector.provenance.program_version == "v1.9-2022.03-dev"


def test_calculation_succeeded(energy_output):
    assert calculation_succeeded(energy_output) is True
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
    assert data_collector.computed.gradient == gradient


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
    assert data_collector.computed.hessian == hessian


@pytest.mark.parametrize(
    "filename,n_atoms",
    (("water.energy.out", 3), ("caffeine.gradient.out", 24)),
)
def test_parse_natoms(test_data_dir, filename, n_atoms, data_collector):
    with open(test_data_dir / filename) as f:
        tcout = f.read()

    parse_natoms(tcout, data_collector)
    assert data_collector.computed.calcinfo_natoms == n_atoms


@pytest.mark.parametrize(
    "filename,nmo",
    (("water.energy.out", 13), ("caffeine.gradient.out", 146)),
)
def test_parse_nmo(test_data_dir, filename, nmo, data_collector):
    with open(test_data_dir / filename) as f:
        tcout = f.read()

    parse_nmo(tcout, data_collector)
    assert data_collector.computed.calcinfo_nmo == nmo


@pytest.mark.parametrize(
    "filename,charge",
    (("water.energy.out", 0), ("caffeine.gradient.out", 0)),
)
def test_parse_molecule_charge(test_data_dir, filename, charge):
    with open(test_data_dir / filename) as f:
        tcout = f.read()
    n = parse_molecule_charge(tcout)
    assert n == charge


@pytest.mark.parametrize(
    "filename,multiplicity",
    (("water.energy.out", 1), ("caffeine.gradient.out", 1)),
)
def test_parse_molecule_spin_multiplicity(test_data_dir, filename, multiplicity):
    with open(test_data_dir / filename) as f:
        tcout = f.read()
    n = parse_molecule_spin_multiplicity(tcout)
    assert n == multiplicity
