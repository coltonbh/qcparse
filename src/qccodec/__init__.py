from importlib import metadata

__version__ = metadata.version(__name__)


from .codec import decode, encode  # noqa: F401
from .registry import registry  # noqa: F401

__all__ = ["decode", "encode", "registry"]
