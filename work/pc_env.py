"""Portable workspace helpers for Perfect Crystal 2020 Japanese port scripts.

All ROMs, reference source trees and third-party dependencies live in a private
local workspace pointed to by the ``PC_WORKSPACE`` environment variable.  When
the variable is unset the repository root is used as a convenience default, so
scripts can be syntax-checked without inputs; they will fail at runtime unless
the required private files are supplied.

The only other override is ``PC_RGBDS``, which points to the legacy RGBDS 0.2.5
binary directory.  Everything else is resolved as a fixed relative path inside
``PC_WORKSPACE``:

  - work/pokemon-reverse-engineering-tools/   (pokemontools)
  - work/perfect_crystal_ue_patched.gbc       (Perfect Crystal 2020 patched ROM)
  - lazy_ips/                                 (lazy_ips)
  - pokekuristaru/                            (labels/charmap/tilesets)
  - perfect_crystal_source/                   (Perfect Crystal 2020 source)
  - rgbds-0.2.5/                              (RGBDS binaries)
"""
import os
from pathlib import Path


def _default_workspace():
    # pc_env.py lives at <repo>/work/pc_env.py
    return Path(__file__).resolve().parent.parent


def workspace():
    """Return the private workspace root as a Path."""
    return Path(os.environ.get("PC_WORKSPACE", _default_workspace()))


def rgbds_dir():
    """Path to the legacy RGBDS 0.2.5 binary directory."""
    override = os.environ.get("PC_RGBDS")
    if override:
        return Path(override)
    return workspace() / "rgbds-0.2.5"
