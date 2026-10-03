# SPDX-FileCopyrightText: 2026 Nye Warburton
# SPDX-License-Identifier: Apache-2.0
"""data: dataset I/O, provenance cards and the license gate.

Part of the base install. LeRobotDataset v3 I/O needs LeRobot, which needs
PyTorch, so it is imported lazily and requires the `behavior` extra.
"""

from saltmarsh.data.lerobot_io import load_lerobot_dataset
from saltmarsh.data.license_gate import (
    ALLOWED_LICENSES,
    LicenseBlockedError,
    check_license,
    is_allowed,
)
from saltmarsh.data.provenance import Asset, ProvenanceCard

__all__ = [
    "ALLOWED_LICENSES",
    "Asset",
    "LicenseBlockedError",
    "ProvenanceCard",
    "check_license",
    "is_allowed",
    "load_lerobot_dataset",
]
