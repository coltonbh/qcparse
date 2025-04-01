import subprocess

from qccodec.codec import decode


def test_cli(test_data_dir):
    # Call CLI script as a subprocess
    filepath = test_data_dir / "terachem" / "water.energy.out"
    result = subprocess.run(
        ["qccodec", "terachem", "energy", filepath], capture_output=True, text=True
    )
    # Check the return code
    assert result.returncode == 0

    # Check the output
    parse_result = decode("terachem", "energy", stdout=filepath.read_text())
    expected_output = parse_result.model_dump_json(indent=4, exclude_unset=True, exclude_defaults=True)
    assert result.stdout.strip() == expected_output
