import os
from pathlib import Path

from qcparse.utils import get_file_contents


def test_get_file_contents_with_bytes():
    """Test get_file_contents with bytes"""
    file_content, filepath = get_file_contents(b"test")
    assert file_content == b"test"
    assert filepath is None


def test_get_file_contents_with_path_to_bytes(tmp_path):
    """Test get_file_contents with a Path to bytes"""
    # Write bytes to a file in temporary directory
    path = tmp_path / "test"
    # Write binary data that can't be decoded to unicode
    data = b"\x80"
    path.write_bytes(data)
    file_content, filepath = get_file_contents(path)
    assert file_content == data
    assert filepath == path


def test_file_contents_with_path_object(test_data_dir):
    """Test get_file_contents with a Path object"""
    path = Path(test_data_dir / "water.energy.out")
    file_content, filepath = get_file_contents(path)
    assert file_content == path.read_text()
    assert filepath == path


def test_file_contents_with_str_for_path(test_data_dir):
    """Test get_file_contents with a str for the path"""
    path = str(test_data_dir / "water.energy.out")
    file_content, filepath = get_file_contents(path)
    assert file_content == Path(path).read_text()
    assert filepath == Path(path)


def test_file_contents_with_short_str_not_filepath():
    """Test get_file_contents with a short str that is not a filepath"""
    file_content, filepath = get_file_contents("test")
    assert file_content == "test"
    assert filepath is None


def test_file_contents_with_long_str_not_filepath():
    """Test get_file_contents with a long str that is not a filepath"""
    test_data = "x" * (os.pathconf(".", "PC_PATH_MAX") + 1)
    file_content, filepath = get_file_contents(test_data)
    assert file_content == test_data
    assert filepath is None
