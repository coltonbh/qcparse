from qcparse.parsers.crest import parse_version_string


def test_parse_version_string(test_data_dir):
    text = (test_data_dir / "crest_stdout.txt").read_text()
    assert parse_version_string(text) == "3.0.1"
