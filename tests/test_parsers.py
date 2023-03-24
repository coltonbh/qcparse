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
    parse_hessian,
    parse_method,
    parse_version,
    parse_xyz_filepath,
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
def test_parse_energy(test_data_dir, filename, energy):
    with open(test_data_dir / filename) as f:
        tcout = f.read()
    assert parse_energy(tcout) == energy


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
    "filename,driver",
    (
        ("water.energy.out", SupportedDrivers.energy),
        ("water.gradient.out", SupportedDrivers.gradient),
        ("water.frequencies.out", SupportedDrivers.hessian),
    ),
)
def test_parse_driver(test_data_dir, filename, driver):
    with open(test_data_dir / filename) as f:
        string = f.read()
    assert parse_driver(string) == driver


def test_parse_driver_raises_exception():
    with pytest.raises(MatchNotFoundError):
        parse_driver("No driver here")


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
        ("water.energy.out", "B3LYP"),
        ("water.gradient.out", "B3LYP"),
        ("water.frequencies.out", "B3LYP"),
    ),
)
def test_parse_method(test_data_dir, filename, method):
    with open(test_data_dir / filename) as f:
        tcout = f.read()
    assert parse_method(tcout) == method


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
    "filename,result",
    (
        (
            "failure.nocuda.out",
            "CUDA error: no CUDA-capable device is detected, file tensorbox/src/tensorbox.cpp, line 33",
        ),
        (
            "failure.basis.out",
            "DIE called at line number 185 in file terachem/basis.cpp",
        ),
    ),
)
def test_parse_failure_text(test_data_dir, filename, result):
    with open(test_data_dir / filename) as f:
        tcout = f.read()
    assert parse_failure_text(tcout) == result


def test_parse_failure_text_non_standard():
    text = parse_failure_text("Not a regular failure message")
    # Assert that some failure message was returned to the users
    assert isinstance(text, str)


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
def test_parse_gradient(test_data_dir, filename, gradient):
    with open(test_data_dir / filename) as f:
        tcout = f.read()
    assert parse_gradient(tcout) == gradient


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
def test_parse_hessian(test_data_dir, filename, hessian):
    with open(test_data_dir / filename) as f:
        tcout = f.read()
    assert parse_hessian(tcout) == hessian
    print("hi")
