# https://github.com/python-poetry/poetry/pull/2366#issuecomment-652418094
from importlib import metadata

__version__ = metadata.version(__name__)


from .main import parse, parse_results  # noqa: F401
from .models import registry  # noqa: F401

__all__ = ["parse", "parse_results", "registry"]
