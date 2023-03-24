import json
import subprocess

from tcparse.main import parse


def test_cli(test_data_dir):
    # Call CLI script as a subprocess
    filepath = str(test_data_dir / "water.energy.out")
    result = subprocess.run(["tcparse", filepath], capture_output=True, text=True)

    # Check the return code
    assert result.returncode == 0

    # Check the output
    parse_result = parse(filepath)
    expected_output = json.dumps(json.loads(parse_result.json()), indent=4)
    assert result.stdout.strip() == expected_output


def test_cli_ignore_xyz(test_data_dir):
    # Call CLI script as a subprocess
    filepath = test_data_dir / "water.energy.out"
    result = subprocess.run(
        ["tcparse", "--ignore_xyz", str(filepath)], capture_output=True, text=True
    )

    # Check the return code
    assert result.returncode == 0

    # Check the output
    parse_result = parse(filepath, ignore_xyz=True)
    expected_output = json.dumps(json.loads(parse_result.json()), indent=4)
    assert result.stdout.strip() == expected_output
