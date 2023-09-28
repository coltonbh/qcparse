import subprocess

from qcparse.main import parse


def test_cli(test_data_dir):
    # Call CLI script as a subprocess
    filepath = str(test_data_dir / "water.energy.out")
    result = subprocess.run(
        ["qcparse", "terachem", filepath], capture_output=True, text=True
    )
    # Check the return code
    assert result.returncode == 0

    # Check the output
    parse_result = parse(filepath, "terachem")
    expected_output = parse_result.model_dump_json(indent=4)
    assert result.stdout.strip() == expected_output
