import pytest

from qcparse.exceptions import DataCollectorError
from qcparse.models import DataCollector


def test_data_collector_only_allows_one_value_per_key():
    dc = DataCollector()
    dc.add_data("energy", -74.964814)
    assert dc["energy"] == -74.964814

    with pytest.raises(DataCollectorError):
        dc.add_data("energy", -24.964814)
