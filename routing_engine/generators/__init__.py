"""Client serializers. Routing decisions belong to the core model."""

from .base import Generator, GeneratedFile
from .happ import HappGenerator
from .xray import XrayGenerator

GENERATORS: dict[str, type[Generator]] = {
    "happ": HappGenerator,
    "xray": XrayGenerator,
}

__all__ = ["GENERATORS", "GeneratedFile", "Generator"]
