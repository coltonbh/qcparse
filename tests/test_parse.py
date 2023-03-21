import pytest

from tcparse.exceptions import MatchNotFoundError
from tcparse.parsers import parse_energy


def test_parse_energy_negative(energy_output):
    energy = parse_energy(energy_output)
    assert energy == -76.3854579982


def test_parse_energy_positive():
    energy = parse_energy("FINAL ENERGY: 76.3854579982 a.u")
    assert energy == 76.3854579982


def test_parse_energy_integer():
    energy = parse_energy("FINAL ENERGY: -7638 a.u")
    assert energy == -7638
    energy = parse_energy("FINAL ENERGY: 7638 a.u")
    assert energy == 7638


def test_parse_energy_exception():
    with pytest.raises(MatchNotFoundError):
        parse_energy("No energy here")
