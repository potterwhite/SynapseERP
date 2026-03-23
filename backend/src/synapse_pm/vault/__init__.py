"""
vault package: Obsidian vault read/write utilities.
"""

from .reader import VaultReader
from .writer import VaultWriter

__all__ = ["VaultReader", "VaultWriter"]
