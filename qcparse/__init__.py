# https://github.com/python-poetry/poetry/pull/2366#issuecomment-652418094
from importlib import metadata

__version__ = metadata.version(__name__)


from .main import parse, parse_computed_props  # noqa: F401
from .registry import registry  # noqa: F401

__all__ = ["parse", "parse_computed_props", "registry"]
