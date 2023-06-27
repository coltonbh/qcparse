from pathlib import Path
from typing import Union

from qcio import Molecule

hydrogen_atom = Molecule(symbols=["H"], geometry=[[0, 0, 0]])


def get_file_content(data_or_path: Union[str, bytes, Path]) -> Union[str, bytes]:
    """Return the file content from a path, str, or bytes."""
    file_content: Union[str, bytes]

    if isinstance(data_or_path, bytes):
        return data_or_path

    filepath = Path(data_or_path)
    try:
        if filepath.is_file():
            # Read the file contents
            file_content = filepath.read_bytes()
            try:
                file_content = file_content.decode("utf-8")
            except UnicodeDecodeError:
                pass
        else:
            file_content = str(data_or_path)
    except OSError:
        # String too long to be filepath
        file_content = str(data_or_path)

    return file_content
