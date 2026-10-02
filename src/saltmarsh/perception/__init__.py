# SPDX-FileCopyrightText: 2026 Coastal Agentics
# SPDX-License-Identifier: Apache-2.0
"""perception: cameras, depth, point clouds and top-down maps (stub).

Needs the `perception` extra (Rerun for viewing, Open3D for point clouds).
"""

from typing import Any

from saltmarsh._extras import require


def rerun() -> Any:
    """Return the `rerun` module (the Rerun SDK), installed by the `perception` extra."""
    return require("rerun", "perception")


def open3d() -> Any:
    """Return the `open3d` module, installed by the `perception` extra."""
    return require("open3d", "perception")


__all__ = ["open3d", "rerun"]
