from qcparse.main import parse


def test_main_terachem_energy(terachem_energy_stdout):
    computed_props = parse(terachem_energy_stdout, "terachem")
    assert computed_props.energy == -76.3861099088
