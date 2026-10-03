# SPDX-FileCopyrightText: 2026 Nye Warburton
# SPDX-License-Identifier: Apache-2.0
"""LeRobotDataset v3 I/O (stub).

LeRobot depends on PyTorch, so it is not part of the base install. This module
imports it only when called; install `saltmarsh[behavior]` to use it.
"""

from typing import Any

from saltmarsh._extras import require
from saltmarsh.data.license_gate import check_license


def load_lerobot_dataset(repo_id: str, *, license: str, **kwargs: Any) -> Any:
    """Open a LeRobotDataset after its declared license passes the gate.

    The caller states the dataset's SPDX license; the gate runs before LeRobot
    is imported or anything is downloaded.
    """
    check_license(license)
    module = require("lerobot.datasets.lerobot_dataset", "behavior")
    return module.LeRobotDataset(repo_id, **kwargs)
