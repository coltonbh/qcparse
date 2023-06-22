import pytest

from qcparse.models import ParsedDataCollector, single_point_data_collector


def test_pdc_only_allows_attribute_to_be_set_once():
    pdc = ParsedDataCollector()
    pdc.energy = -74.964814
    assert pdc.energy == -74.964814

    with pytest.raises(AttributeError):
        pdc.energy = -74.964814


# def test_pdc_dict_serialization_method():
#     pdc = ParsedDataCollector()
#     pdc.nested = ParsedDataCollector()

#     pdc.value = 1
#     pdc.array = [1, 2, 3]
#     pdc.nested.energy = -74.964814
#     pdc.nested.map = {"key": [1, 2, 3]}

#     pdc_dict = pdc.dict()
#     assert pdc_dict["value"] == 1
#     assert pdc_dict["nested"]["energy"] == -74.964814


def test_pdc_dict_serialization_method():
    pdc = ParsedDataCollector()
    pdc.nested = ParsedDataCollector()
    pdc.nested_list = [ParsedDataCollector(), ParsedDataCollector()]

    pdc.value = 1
    pdc.array = [1, 2, 3]
    pdc.nested.energy = -74.964814
    pdc.nested.map = {"key": [1, 2, 3]}
    pdc.nested_list[0].value = 2
    pdc.nested_list[1].value = 3

    pdc_dict = pdc.dict()
    # import pdb; pdb.set_trace()
    assert pdc_dict["value"] == 1
    assert pdc_dict["nested"]["energy"] == -74.964814
    assert pdc_dict["nested_list"][0]["value"] == 2
    assert pdc_dict["nested_list"][1]["value"] == 3


def test_single_point_data_collector_no_inputs():
    pdc = single_point_data_collector(collect_inputs=False)
    assert pdc.computed == ParsedDataCollector()
    assert pdc.provenance == ParsedDataCollector()
    assert pdc.extras == ParsedDataCollector()
    assert not hasattr(pdc, "input_data")
