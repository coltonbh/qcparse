from qcparse.main import parse_results


def test_pcp_terachem_energy(terachem_energy_stdout):
    computed_props = parse_results(terachem_energy_stdout, "terachem")
    assert computed_props.energy == -76.3861099088
