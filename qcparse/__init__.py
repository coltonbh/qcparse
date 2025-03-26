# https://github.com/python-poetry/poetry/pull/2366#issuecomment-652418094
from importlib import metadata

__version__ = metadata.version(__name__)


from .main import decode, encode  # noqa: F401
from .models import registry  # noqa: F401

__all__ = ["decode", "encode", "registry"]
