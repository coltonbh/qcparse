from pathlib import Path

import pytest

from tcparse.exceptions import MatchNotFoundError
from tcparse.parsers import (
    SupportedDrivers,
    calculation_succeeded,
    parse_basis,
    parse_driver,
    parse_energy,
    parse_failure_text,
    parse_gradient,
    parse_method,
    parse_version,
    parse_xyz_filepath,
)


@pytest.mark.parametrize(
    "filename,energy",
    (
        ("energy.out", -76.3861099088),
        ("gradient.out", -76.3861099088),
        ("frequencies.out", -76.3861099088),
    ),
)
def test_parse_energy(test_data_dir, filename, energy):
    with open(test_data_dir / filename) as f:
        tcstdout = f.read()
    assert parse_energy(tcstdout) == energy


def test_parse_energy_positive():
    energy = parse_energy("FINAL ENERGY: 76.3854579982 a.u")
    assert energy == 76.3854579982


def test_parse_energy_integer():
    energy = parse_energy("FINAL ENERGY: -7638 a.u")
    assert energy == -7638
    energy = parse_energy("FINAL ENERGY: 7638 a.u")
    assert energy == 7638


def test_parse_energy_raises_exception():
    with pytest.raises(MatchNotFoundError):
        parse_energy("No energy here")


@pytest.mark.parametrize(
    "filename,runtype",
    (
        ("energy.out", SupportedDrivers.energy),
        ("gradient.out", SupportedDrivers.gradient),
        ("frequencies.out", SupportedDrivers.hessian),
    ),
)
def test_parse_runtype(test_data_dir, filename, runtype):
    with open(test_data_dir / filename) as f:
        string = f.read()
    assert parse_driver(string) == runtype


def test_parse_runtype_raises_exeption():
    with pytest.raises(MatchNotFoundError):
        parse_driver("No runtype here")


@pytest.mark.parametrize(
    "string,path",
    (
        ("XYZ coordinates water.xyz", Path("water.xyz")),
        ("XYZ coordinates water", Path("water")),
        ("XYZ coordinates /scratch/water.xyz", Path("/scratch/water.xyz")),
        ("XYZ coordinates ../water.xyz", Path("../water.xyz")),
    ),
)
def test_parse_xyz(string, path):
    assert parse_xyz_filepath(string) == path


@pytest.mark.parametrize(
    "filename,method",
    (
        ("energy.out", "B3LYP"),
        ("gradient.out", "B3LYP"),
        ("frequencies.out", "B3LYP"),
    ),
)
def test_parse_method(test_data_dir, filename, method):
    with open(test_data_dir / filename) as f:
        tcstdout = f.read()
    assert parse_method(tcstdout) == method


def test_parse_basis(energy_output):
    assert parse_basis(energy_output) == "6-31g"


def test_parse_version(energy_output):
    assert parse_version(energy_output) == "v1.9-2022.03-dev"


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


def test_parse_failure_text():
    string = "DIE called at line number 3572 in file terachem/params.cpp"
    assert (
        parse_failure_text(
            """
        Incorrect purify value
        DIE called at line number 3572 in file terachem/params.cpp
         Job terminated: Thu Mar 23 03:47:12 2023
        """
        )
        == string
    )


@pytest.mark.parametrize(
    "filename,gradient",
    (
        (
            "gradient.out",
            [
                [-2.69528e-05, -3.88595e-05, 3.06421e-05],
                [1.15012e-05, 2.39264e-05, 4.2012e-06],
                [1.5448e-05, 1.49307e-05, -3.48414e-05],
            ],
        ),
        (
            "caffeine.gradient.out",
            [
                [-0.0027556954, -0.0383229638, 4.20531e-05],
                [0.0092623711, -0.0018411177, 1.3252e-05],
                [0.0060595033, -0.0181530205, 5.40354e-05],
                [-0.0248832858, 0.0100861343, -5.5429e-06],
                [-0.0073723976, 0.0047539295, 9.70834e-05],
                [0.0183934862, 0.0195032976, -1.0283e-05],
                [0.0118731902, -0.0065120943, 4.17644e-05],
                [0.0230149612, 0.014090794, -1.96014e-05],
                [0.0054623265, 0.0383403113, -0.0001376433],
                [-0.0261084937, -0.0032217398, -6.94864e-05],
                [-0.019741059, -0.0088425162, 9.4621e-06],
                [0.0006240535, 0.0095965187, -8.329e-06],
                [-0.0033976872, -0.0096027254, -7.1007e-06],
                [0.0192649847, -0.0003004125, -2.07558e-05],
                [0.0026288768, -0.0016107423, 5.0651e-06],
                [-0.0006730478, 0.0023432321, -0.0020739172],
                [-0.0028407626, -0.0074904487, 7.7725e-06],
                [-0.0006749384, 0.0023440655, 0.002078061],
                [0.0015282959, 0.0003929277, 1.8356e-06],
                [-0.0030804706, -0.0046068943, -0.0035988921],
                [-0.0030854975, -0.0046109791, 0.0036040234],
                [-0.0067750261, 0.0074798652, -2.6833e-06],
                [0.0016434089, -0.0019167997, 0.0014402283],
                [0.0016329015, -0.0018986239, -0.0014404005],
            ],
        ),
    ),
)
def test_parse_gradient(test_data_dir, filename, gradient):
    with open(test_data_dir / filename) as f:
        tcstdout = f.read()
    assert parse_gradient(tcstdout) == gradient
