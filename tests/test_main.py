from qcparse.main import parse_computed_props


def test_pcp_terachem_energy(energy_output):
    computed_props = parse_computed_props(energy_output, "terachem")
    assert computed_props.energy == -76.3861099088
